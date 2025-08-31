# campus-network-auto

一个可以实现校园网开机自动连接的程序。目前可实现的高校有：HBUT、ZUEL，校园网采用深澜系统的其他高校可以修改配置文件直接运行或根据源码自己调试。

0.（开发选项，直接使用可以忽略）在当前脚本的IDE终端下输入以下这行命令，可以打包到指定的安装路径，且启动时可避免弹窗：

	pyinstaller --onefile --noconsole --distpath=（你的目标路径）"D:\Pycharm\Pycharm Projects\pythonLearning\XXXX_Network " （当前脚本名称）autoNetwork.py 

1.在“校园网配置文件”中输入自己的HBUT或ZUEL校园网学号和密码，若在不同地点有不同ssid，请使用中文逗号分隔多个WiFi名称。其他高校可以自行修改自己学校校园网的WiFi名称。

2.使用注册表编辑器添加开机自启动功能：

	通过修改注册表可以实现开机启动程序的配置。

	按下 Win + R 键，输入 regedit，然后按回车。

	导航至以下路径：HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run。

	在右侧窗格中右键选择“新建” > “字符串值”，输入一个名称（如程序名称）。

	双击该字符串值，在“数值数据”栏中输入目标 .exe 文件（如autoNetwork.exe）的完整路径，然后点击“确定”。

	重启计算机后配置生效。

3.目前仅支持edge或Chrome浏览器驱动，确保这些浏览器安装在你的电脑里。

4.有问题可联系-QQ：2787493907
