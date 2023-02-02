import sensor,image,lcd  # import 相关库
import KPU as kpu
import time
from Maix import FPIOA,GPIO
import gc
from fpioa_manager import fm
import utime


task_fd = kpu.load("/sd/FaceDetection.smodel")# 加载人脸检测模型
task_ld = kpu.load("/sd/FaceLandmarkDetection.smodel")# 加载人脸五点关键点检测模型
task_fe = kpu.load("/sd/FeatureExtraction.smodel")

clock = time.clock()  # 初始化系统时钟，计算帧率
#将 LED 外部 IO 注册到内部 GPIO， K210 引脚支持任意配置
fm.register(12, fm.fpioa.GPIO0)
fm.register(13, fm.fpioa.GPIO1)
fm.register(14, fm.fpioa.GPIO2)
LED_B = GPIO(GPIO.GPIO0, GPIO.OUT,value=1) #构建 LED 对象
LED_G = GPIO(GPIO.GPIO1, GPIO.OUT,value=1) #构建 LED 对象
LED_R = GPIO(GPIO.GPIO2, GPIO.OUT,value=1) #构建 LED 对象

key_pin=16 # 设置按键引脚 FPIO16
fm.register(key_pin, fm.fpioa.GPIOHS0)#注册 IO，注意高速 GPIO 口才有中断
KEY=GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.IRQ_RISING)

lcd.init() # 初始化lcd
sensor.reset() #初始化sensor 摄像头
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_hmirror(0) #设置摄像头镜像
sensor.set_vflip(0)   #设置摄像头翻转
sensor.run(1) #使能摄像头
anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025) #anchor for face detect 用于人脸检测的Anchor
dst_point = [(44,59),(84,59),(64,82),(47,105),(81,105)] #standard face key point position 标准正脸的5关键点坐标 分别为 左眼 右眼 鼻子 左嘴角 右嘴角
a = kpu.init_yolo2(task_fd, 0.5, 0.3, 5, anchor) #初始化人脸检测模型
img_lcd=image.Image() # 设置显示buf
img_face=image.Image(size=(128,128)) #设置 128 * 128 人脸图片buf
a=img_face.pix_to_ai() # 将图片转为kpu接受的格式


# 按键按下标志
key_Flag=0
#按键状态标志 1单击2长按
key_pressed=0
t=utime.ticks_ms()
#按键中断回调函数
def fun(KEY):
    global key_Flag
    global key_pressed
    global t
    if KEY.value()==0:
       utime.sleep_ms(5) #消除抖动
       if KEY.value()==0: #确认按键被按下
          if key_Flag==0:
             key_Flag=1            #按键标志位加1
             t = utime.ticks_ms()  #记录被被按下的时间

    if KEY.value()==1:
       utime.sleep_ms(5) #消除抖动
       if KEY.value()==1: #确认按键被抬起
          if key_Flag==1:
             if (utime.ticks_ms()-t)>2000:
                key_pressed=2 #长按
                key_Flag=0
             else:
                key_pressed=1 #单击
                key_Flag=0

#开启中断，上下沿都触发
KEY.irq(fun, GPIO.IRQ_BOTH)


class People:#创建类，用来将姓名和特征对应起来
      name=[]
      feature=[]
      def __init__(self):
         pass

      def feature_max(self,feature):
         if self.feature==[]: #人脸被删除会无法对比，需要判断
            return 0
         score = kpu.face_compare(self.feature, feature) #计算当前人脸特征值与已存特征值的分数
         return score

peoples = [] # 人名标签，储存人名。

i=0#用来计量储存到了第几人
#读取人脸信息和特征值
with open("/sd/recordftr.txt", "r") as f:
    while(1):
        readtxt = f.readline()
        if not readtxt:
            break
        exec("people%s=[]"%i) #创建peoplei列表
        exec("peoples.append(people%s)"%i) #将peoplei储存到人脸库
        peoples[i]=People()  #实例化读取到的标签

        stu_name = readtxt[0:readtxt.index('#')]      #获取姓名
        peoples[i].name=stu_name

        readtxt = readtxt[readtxt.index('#')+1:]      #截取除了姓名以外的字符串
        peoples[i].feature=eval(readtxt)              #保存特征

        print("%d:%s,%s" % (i,peoples[i].name,str(peoples[i].feature))) #输出查看读取到的人脸数据
        i+=1

def Addface(i,feature): #添加人脸函数
    exec("people%s=[]"%i) #创建peoplei列表
    exec("peoples.append(people%s)"%i) #将peoplei储存到人脸库
    peoples[i]=People()  #实例化新人
    peoples[i].name=("ID%s"%i)
    peoples[i].feature=feature

    #写入SD卡
    with open("/sd/recordftr.txt", "a") as f:
        f.write(('ID%s'%i)+'#'+str(feature))  #信息写入SD卡
        f.write("\n")
        f.close()

def Deleteface(i):   #删除人脸函数
    with open("/sd/recordftr.txt","r",encoding="utf-8") as f:#将SD卡人脸数据清空
        lines = f.readlines()
    with open("/sd/recordftr.txt","w",encoding="utf-8") as f_w:
        for line in lines:
            if str(peoples[i].name) in line:
                continue
            f_w.write(line)

    peoples[i].name="Null"
    peoples[i].feature=[]#将系统人脸数据清空



def Face_detection(img):
    max_score = 0 #记录最高分
    code = kpu.run_yolo2(task_fd, img) # 运行人脸检测模型，获取人脸坐标位置
    if code: # 如果检测到人脸
        for i in code: # 迭代坐标框
            # Cut face and resize to 128x128
            a = img.draw_rectangle(i.rect()) # 在屏幕显示人脸方框
            face_cut=img.cut(i.x(),i.y(),i.w(),i.h()) # 裁剪人脸部分图片到 face_cut
            face_cut_128=face_cut.resize(128,128) # 将裁出的人脸图片 缩放到128 * 128像素
            a=face_cut_128.pix_to_ai() # 将猜出图片转换为kpu接受的格式
            #a = img.draw_image(face_cut_128, (0,0))
            # Landmark for face 5 points
            fmap = kpu.forward(task_ld, face_cut_128) # 运行人脸5点关键点检测模型
            plist=fmap[:] # 获取关键点预测结果
            le=(i.x()+int(plist[0]*i.w() - 10), i.y()+int(plist[1]*i.h())) # 计算左眼位置， 这里在w方向-10 用来补偿模型转换带来的精度损失
            re=(i.x()+int(plist[2]*i.w()), i.y()+int(plist[3]*i.h())) # 计算右眼位置
            nose=(i.x()+int(plist[4]*i.w()), i.y()+int(plist[5]*i.h())) #计算鼻子位置
            lm=(i.x()+int(plist[6]*i.w()), i.y()+int(plist[7]*i.h())) #计算左嘴角位置
            rm=(i.x()+int(plist[8]*i.w()), i.y()+int(plist[9]*i.h())) #右嘴角位置
            #a = img.draw_circle(le[0], le[1], 4)
            #a = img.draw_circle(re[0], re[1], 4)
            #a = img.draw_circle(nose[0], nose[1], 4)
            #a = img.draw_circle(lm[0], lm[1], 4)
            #a = img.draw_circle(rm[0], rm[1], 4) # 在相应位置处画小圆圈
            # align face to standard position
            src_point = [le, re, nose, lm, rm] # 图片中 5 坐标的位置
            T=image.get_affine_transform(src_point, dst_point) # 根据获得的5点坐标与标准正脸坐标获取仿射变换矩阵
            a=image.warp_affine_ai(img, img_face, T) #对原始图片人脸图片进行仿射变换，变换为正脸图像
            a=img_face.ai_to_pix() # 将正脸图像转为kpu格式
            #a = img.draw_image(img_face, (128,0))
            del(face_cut_128) # 释放裁剪人脸部分图片
            # calculate face feature vector
            fmap = kpu.forward(task_fe, img_face) #计算正脸图片的196维特征值
            feature=kpu.face_encode(fmap[:]) #获取计算结果
            index = 0 #记录最高分数编号
            for j in range(len(peoples)): #迭代已存特征值

                score=peoples[j].feature_max(feature)
                if  score>max_score:
                    max_score = score
                    index = j #记录最高分数编号
            break
        return [max_score,i.x(),i.y(),index,feature]#返回最高分
    else:
        max_score=-1
        return [max_score,0,0,0,0] #返回无人脸



while(1): # 主循环
    if key_pressed==0:
       img = sensor.snapshot() #从摄像头获取一张图片
       value=Face_detection(img)
       if value[0] > 85: # 如果最大分数大于85， 可以被认定为同一个人
           img.draw_string(value[1],value[2], ("%s :%2.1f" % (peoples[value[3]].name, value[0])), color=(0,255,0),scale=2) # 显示人名 与 分数
       elif value[0] >= 0:
           img.draw_string(value[1],value[2], ("NO :%2.1f" % (value[0])), color=(255,0,0),scale=2) #显示未知 与 分数
       lcd.display(img) #刷屏显示

    if key_pressed==1:#单击添加人脸
       key_pressed=0
       while(1):
           img = sensor.snapshot() #从摄像头获取一张图片
           value=Face_detection(img)
           img.draw_string(0,0, "Add face", color=(0,0,255),scale=3) #添加人脸
           if key_pressed==1:
              if value[0] > 85: # 如果人脸已经存在
                 img.draw_string(value[1],value[2], ("%s exists" % (peoples[value[3]].name)), color=(255,0,0),scale=2) # 显示人名
                 LED_R.value(0)
              elif value[0] >= 0:
                 Addface(i,value[4])
                 i+=1
                 img.draw_string(value[1],value[2], "Add OK", color=(0,255,0),scale=2) # 添加成功
                 LED_G.value(0)
              key_pressed=0
              lcd.display(img) #刷屏显示
              utime.sleep_ms(1000)
              LED_R.value(1)
              LED_G.value(1)
              break
           lcd.display(img) #刷屏显示

    if key_pressed==2:#长按删除人脸
       key_pressed=0
       namei=-1
       while(1):
           img.clear()
           img.draw_string(0,0, "Delete face", color=(255,0,0),scale=3) #删除人脸
           img.draw_string(40,60, "Please select a number", color=(0,0,255),scale=2) #选择一个编号
           if key_pressed==1:
              key_pressed=0
              namei+=1
           if namei==-1:
              img.draw_string(120,110, "cancel", color=(50,0,255),scale=2) #选择一个编号
           elif namei<i:  #不超过保存的最大值
              img.draw_string(120,110, ("%s:%s"%(str(namei),peoples[namei].name)), color=(50,0,255),scale=2) #显示编号和姓名
           else:
              namei=-1
           if key_pressed==2:
              key_pressed=0
              if namei>=0:
                 Deleteface(namei)
                 img.draw_string(40,140, ("Delete %s succeeded"%(peoples[namei].name)), color=(0,255,0),scale=2) #删除成功
                 LED_G.value(0)
              lcd.display(img) #刷屏显示
              utime.sleep_ms(1000)
              LED_G.value(1)
              break
           lcd.display(img) #刷屏显示

    gc.collect()
