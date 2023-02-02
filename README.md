# K210-face-recognition
使用k210做的人脸识别打卡机，可以实现在线添加人脸数据、删除人脸数据、断电存储数据等功能。

人脸识别模型使用spieed官方模型仓库的模型。获取地址如下  https://maixhub.com/model/zoo/60 
获取模型后将模型放入SD卡，因模型文件名称更新原因，需要将模型文件名称和程序中的名称对应起来
![image](https://user-images.githubusercontent.com/57904131/216210434-a3ab266e-8f2c-4961-b0a0-726e587341fd.png)

其次在SD卡中创建recordftr.txt文件，用来保存人脸特征数据，实现断电续存。

接着就可以运行程序，
按键单击进入人脸添添加功能，再次单击会进行人脸数据添加，如果未检测到人脸或者当前人脸已经存在，那么保存失败。因为没有输入设备，人脸添加后会自动以ID形式命名，记住当前人脸与他对应的ID号码，打开sd卡的TXT文件，修改ID号为真实姓名（仅支持英文），再次开机即可成功显示。
![1675243079068_AD53C4E1-F335-4442-97E3-A1F8C31FEC67](https://user-images.githubusercontent.com/57904131/216211036-3eb69786-ebf2-4e65-b9a3-724228e8db3d.png)

按键长按2秒进入人脸删除功能，第一个选项为取消，再次单击，会依次遍历储存库中的人脸姓名，选择完成后再次长按两秒，会对选择的人脸数据进行删除.

![lADPJwY7W_WafKPNDIDNBaA_1440_3200](https://user-images.githubusercontent.com/57904131/216212062-c5318dc7-f104-495e-8f97-aacc2eeab230.jpg)
