AV-Separation 视听分离系统部署启动说明
项目简介
后端基于 FastAPI 部署在 AutoDL 云服务器，负责用户登录注册、双视频上传、视频预处理、模型推理、历史记录查询；前端本地运行，通过 AutoDL 公网地址请求后端接口、加载可视化结果图。
环境信息
AutoDL 服务器
项目根路径：/root/autodl-tmp/iQuery-2/
后端服务端口：6006
Python 版本：>=3.9

一、服务器环境准备
进入项目根目录

cd /root/autodl-tmp/iQuery-2/
安装依赖

pip install fastapi uvicorn sqlalchemy pydantic python-multipart opencv-python ffmpeg-python glob2
AutoDL 控制台配置端口映射
实例端口映射面板添加 6006 端口，保存生成外网访问地址。
服务器放行端口

sudo ufw allow 6006/tcp
赋予目录读写权限

chmod 755 -R /root/autodl-tmp/iQuery-2/
二、后端启动命令
方式 1：前台启动（调试，关闭终端服务停止）

cd /root/autodl-tmp/iQuery-2/
python main.py
启动成功标识：Uvicorn running on http://0.0.0.0:6006
方式 2：后台常驻运行（推荐）

cd /root/autodl-tmp/iQuery-2/
nohup python main.py > server.log 2>&1 &
查看实时日志：

tail -f server.log
关闭服务：

lsof -i :6006
kill -9 进程号
三、本地前端配置
复制 AutoDL 外网地址，格式示例：http://xxx.autodl.com:12345
修改前端全局接口请求基地址为上述地址
资源访问路由（后端已内置挂载，无需额外配置）
上传视频预览：http://域名:端口/static/video/xxx
可视化对比图：http://域名:端口/viz/文件夹名/图片.jpg
四、完整使用流程
AutoDL 启动后端服务
本地启动前端项目
注册 / 登录账号
上传 2 个视频提交任务
后端自动执行全流水线：创建批次目录→提取帧 & 音频→光流提取→目标检测→生成 CSV→模型推理→输出可视化对比图
页面自动展示推理结果
历史记录页面查看全部历史任务与对应图片
