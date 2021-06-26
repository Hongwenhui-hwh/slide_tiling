'''
    File name: read_json_and_tile.py
    Date created: 2021/06/26

	Objective:
	Tile svs images with the json masks
	(Marked with pair software)
	

'''


import cv2
import tarfile
import os
import json
import numpy as np
import openslide as opsl
import sys
import time
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw





def get_file_name(file_dir):
    # Parameter:
    # file_dir: the folder path of *.tar
    # return : [List]: all file path
    print('get_file_name')
    L=[]
    for root,dirs,files in os.walk(file_dir):
        for file in files:
            L.append(file)
            return L


def un_tar(file_names, file_path):
    # Parameter:
    # file_names: the file name of *.tar
    # file_path: the save path about the unzipped files.(default: same path of *.tar)
    print('un_tar')
    for name in tarfile.open(file_path+"//"+file_names).getnames():
        tarfile.open(file_path+"//"+file_names).extract(name, file_path )


def read_json(json_file):
    with open(json_file, 'r') as load_f:
        # 转换文件
        load_dict = json.load(load_f)
        Polys = load_dict['Polys']
        #print(coordinate[])
        for i in range(0,len(Polys)):
            Points = Polys[i]['Shapes'][0]['Points']
            for j in range(0,len(Points)):
                point_x=Points[j]['Pos'][0]
                point_y=Points[j]['Pos'][1]
                #print(point_x,point_y)
    return Polys


def openslide_cut_patch_and_save(slide, patch_c, patch_r, step,mask, ID):
    # patch_c,patch_r分别是切片图像的宽和高
    # step是移动的步幅
    path =os.path.join('/opt/data/private/MY_code/PC_task2/adaptive_color_deconvolution-master/test',ID)
    if not os.path.exists(path):
        os.mkdir(ID)
    else:
        print('The folder has been created!')

    width = slide.level_dimensions[0][0]
    height = slide.level_dimensions[0][1]
    print ('W = %d, H = %d'  % (width, height))
    w_count = int(width // step)
    h_count = int(height // step)
    for x in range (1,w_count - 1):
        #一般来说头和尾的部分都是空白，可以适当跳过，当然也可以选择全部处理
        print("\r", end="")
        print("Tiling progress: {}%: ".format(x), "▋" * (x // 5), end="")
        sys.stdout.flush()
        time.sleep(0.00001)
        for y in range (int(h_count)):
            mid_x = int(x * step + patch_c/2)
            mid_y = int(y * step + patch_r/2)
            if ((mid_x+patch_c<width) and (mid_y+patch_r<height) and (mask[mid_y, mid_x, 2])==255):
                #print("This patch is in the annotation area")
                #print(mid_x, mid_y)
                tile = slide.read_region((x * step , y * step) , 0 , (patch_c,patch_r))

                gray = tile.convert('L')     #将 tile 转换为灰度图像，0表示黑，255表示白。
                bw = gray.point(lambda x: 0 if x<220 else 1, 'F')
                avgBkg = np.average(bw)
                # check if the image is mostly background
                if avgBkg <= 0.5:
                    tile = tile.convert('RGB')
                    tile_name = os.path.join(path,str(x)+'_'+str(y)+'.jpg')
                    tile.save(tile_name)

            ## 这样得到切片图slide_region对象后，可以开始下一步骤(保存或者处理分析)

if __name__ == "__main__":
    #examples: Call the above two functions
    '''for My_file_name in get_file_name(os.getcwd()):
        if My_file_name.find(".tar")!=-1:
            un_tar(My_file_name,os.getcwd()) #解压文件'''
    #根据路径读取svs图片
    slide_name= '201310200.svs'
    slide=opsl.OpenSlide(slide_name)
    Wh = np.zeros((len(slide.level_dimensions),2))
    #level_dimensions属性是获取指定级下的图像的宽和高，返回的是一个list，每一个元素是一个数组
    print('level_dimensions: ' + str(0))
    width = slide.level_dimensions[0][0]
    height = slide.level_dimensions[0][1]
    print ('W = %d, H = %d'  % (width, height))

    NewFact = 50
    #os.getcwd() 方法用于返回当前工作目录
    #读取json文件
    json_file = '/opt/data/private/MY_code/PC_task2/adaptive_color_deconvolution-master/test/201310200_svs_Label.json'
    Polys = read_json(json_file)
    for i in range(0,len(Polys)):
        Points = Polys[i]['Shapes'][0]['Points']
        x_total=[]
        y_total=[]
        for j in range(0,len(Points)):
            point_x=Points[j]['Pos'][0]
            point_y=Points[j]['Pos'][1]
            #x_total.append(int(round(point_x/NewFact)))
            #y_total.append(int(round(point_y/NewFact)))
            x_total.append(int(point_x))
            y_total.append(int(point_y))
            #print(point_x,point_y)
        cor_xy = np.vstack((x_total, y_total))


        '''slide=opsl.OpenSlide('201310200.svs')
        height = slide.level_dimensions[0][0]
        width = slide.level_dimensions[0][1]
        NewFact = max(height, width) / min(max(height, width),15000.0)
        img = Image.new('L', (int(height/NewFact), int(width/NewFact)), 0)
        ImageDraw.Draw(img,'L').polygon(cor_xy, outline=255, fill=255)
        mask = np.array(img)
        Image.fromarray(255-mask).save(os.path.join( "mask_1.jpeg"))'''



        # 以5级图像的尺寸作为指定输出的缩略图尺寸返回一个缩略图图像
        slide_thumbnail = slide.get_thumbnail(slide.level_dimensions[5])
        '''plt.imshow(slide_thumbnail)
        plt.show()
        print(slide_thumbnail.size)'''

        #Create a black image
        #mask的x和y是反的
        mask = np.zeros((int(height), int(width), 3), np.uint8)
        pts = np.array([cor_xy],np.int32)
        #顶点数：52，矩阵变成52*1*2维
        pts = pts.transpose((2,0,1))
        # 绘制未填充的多边形
        #cv2.polylines(mask,[pts],True,(255,255,255))   #坐标对是数组形式，我们需要用‘[ ]' 转换为列表形式，然后用np.int32转化格式
        # 绘制填充的多边形,得到最终的mask
        cv2.fillConvexPoly(mask, pts, (255,255,255))
        #显示并保存图像
        #plt.imshow(mask)
        #plt.show()
        #cv2.imwrite('mask_out.tif',mask)

        patch_c=2000
        patch_r=2000
        step=2000
        ID = slide_name[:-4]
        openslide_cut_patch_and_save(slide, patch_c, patch_r, step,mask, ID)



    slide.close()

