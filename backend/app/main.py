import os
import shutil
import uvicorn
import urllib.parse  # <--- 1. 务必导入这个库
from typing import List
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models, database, pipeline

# --- 1. 初始化数据库 ---
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AV-Separation System")

# --- 2. 跨域配置 ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. 静态文件挂载 ---
BASE_DATA_DIR = "data"
os.makedirs(os.path.join(BASE_DATA_DIR, "video"), exist_ok=True)
os.makedirs(os.path.join(BASE_DATA_DIR, "results"), exist_ok=True)

# (1) 挂载基础数据 (上传的视频等)
app.mount("/static", StaticFiles(directory=BASE_DATA_DIR), name="static")

# (2) 【关键】挂载模型可视化结果目录
# 你的可视化结果都在这里
VIZ_ABS_DIR = "/root/autodl-tmp/iQuery-2/data/ckpt/Ema+三重动态(改)/visualization"
if not os.path.exists(VIZ_ABS_DIR):
    os.makedirs(VIZ_ABS_DIR, exist_ok=True)

# 挂载到 /viz 路径，前端通过 /viz/文件夹名/文件名 访问
app.mount("/viz", StaticFiles(directory=VIZ_ABS_DIR), name="viz")

# --- 4. 初始化 Pipeline ---
processor = pipeline.AVSeparationPipeline(base_data_dir=BASE_DATA_DIR)

# --- 5. 数据库依赖 ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserAuth(BaseModel):
    username: str
    password: str

# --- 辅助函数：获取最新的一个结果文件夹 ---
def get_first_result_folder(base_dir):
    try:
        if not os.path.exists(base_dir):
            return None
        # 获取 base_dir 下的所有子文件夹
        subdirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        
        if not subdirs:
            return None
        
        # 按修改时间排序，取最新的一个 (这样能保证拿到的是刚刚跑出来的结果)
        # 如果你确实只是想取“列表里的第一个”不管时间，可以改成 subdirs[0]
        latest_folder = max(subdirs, key=os.path.getmtime)
        return os.path.basename(latest_folder) # 返回文件夹名，例如 "accordion-QaOU..."
    except Exception as e:
        print(f"查找结果文件夹出错: {e}")
        return None

# ================= API 接口 =================

@app.post("/api/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = models.User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "msg": "注册成功", "username": new_user.username}

@app.post("/api/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    return {"status": "success", "msg": "登录成功", "token": str(db_user.id), "username": db_user.username}

@app.post("/api/upload_pair")
async def upload_video_pair(
    files: List[UploadFile] = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    if len(files) != 2:
        raise HTTPException(status_code=400, detail="必须上传两个视频文件")

    # 1. 保存上传文件
    saved_abs_paths = []
    filenames = []
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    for index, file in enumerate(files):
        sub_folder_name = f"{batch_id}_{index}"
        upload_sub_dir = os.path.join(BASE_DATA_DIR, "video", sub_folder_name)
        os.makedirs(upload_sub_dir, exist_ok=True)
        
        file_path = os.path.join(upload_sub_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        saved_abs_paths.append(os.path.abspath(file_path))
        filenames.append(file.filename)

    # 2. 运行模型
    try:
        processor.process_pair(saved_abs_paths)
    except Exception as e:
        print(f"Pipeline Error: {e}")
        raise HTTPException(status_code=500, detail=f"模型处理失败: {str(e)}")

    # 3. 获取结果：只取 visualization 下最新的一个文件夹
    folder_name = get_first_result_folder(VIZ_ABS_DIR)
    
    if not folder_name:
        # 如果没生成，说明出问题了，但为了不报错，可以返回空
        print("警告：未在 visualization 目录下找到结果文件夹")
        folder_name = ""

    # 4. 存入数据库 (只存文件夹名，方便后续拼接)
    video_names_str = f"{filenames[0]} & {filenames[1]}"
    new_record = models.History(
        user_id=user_id,
        video_name=video_names_str,
        input_path=f"/static/video/{batch_id}_0/{filenames[0]}", 
        result_path=folder_name, # 这里存 "accordion-QaOU..."
        created_at=datetime.now()
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # ===【关键修复在这里】===
    # 你必须先定义 safe_folder_name，下一行代码才能使用它
    safe_folder_name = urllib.parse.quote(folder_name)

    # 5. 返回给前端 URLs
    # 构造固定的文件名
    return {
        "status": "success", 
        "data": {
            "record_id": new_record.id,
            "folder": folder_name,
            "urls": {
                # Amp (Map) 对比
                "gtmap1": f"/viz/{safe_folder_name}/gtamp1.jpg",
                "predmap1": f"/viz/{safe_folder_name}/predamp1.jpg",
                "gtmap2": f"/viz/{safe_folder_name}/gtamp2.jpg", 
                "predmap2": f"/viz/{safe_folder_name}/predamp2.jpg",
                
                # Mask 对比
                "gtmask1": f"/viz/{safe_folder_name}/gtmask1.jpg",
                "predmask1": f"/viz/{safe_folder_name}/predmask1.jpg",
                "gtmask2": f"/viz/{safe_folder_name}/gtmask2.jpg",
                "predmask2": f"/viz/{safe_folder_name}/predmask2.jpg"
            }
        }
    }

@app.get("/api/history")
def get_history(user_id: int, db: Session = Depends(get_db)):
    records = db.query(models.History).filter(models.History.user_id == user_id).order_by(models.History.created_at.desc()).all()
    return records

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6006)