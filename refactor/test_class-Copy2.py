
#encoding:utf-8
import torch as t
import time
import numpy as np
# from models import MutltiCNN as Classifier
from models  import Classifier as Classifier1
from models import iso_Classifier_1 as Classifier3
from models import Luna2016 as Classifier2
#from models import L2 as Classifier
import torch
import csv
import sys
sys.path.append("../")
# !TODO del this 或迁移至 data/util.py
from data.util import get_filename,voxel_2_world
########## end ################
from glob import glob
import os
import fire
from data.util import get_topn,normalize,zero_normalize
try:
    from tqdm import tqdm # long waits are not fun
except:
    print('tqdm 是一个轻量级的进度条小包。。。')

class Config:
    #model_dir1="checkpoints/classifier_0705_00:33:42.pth"#模型保存路径
    model_dir1="checkpoints/classifier_0705_00:33:42.pth"
    model_dir2="checkpoints/luna2016_0701_09:32:03.pth"
    model_dir3="checkpoints/iso_classifier_0716_13:53:02.pth"
    img_dir='/mnt/7/0704_test_64_80/'#数据父路径
    topN=100#每个病人选取多少个结点
    batch_size=8
    csv_file="test_0716_1_no.csv"#分类结果csv保存路径
    prob_threshould=0.0#概率阈值，只保存大于此概率的结点
    limit = 1000 # 最多测试多少个文件

9
opt = Config() 
def parse(kwargs):
    ## 处理配置和参数
    for k,v in kwargs.iteritems():
        if not hasattr(opt,k):
            print("Warning: opt has not attribut %s" %k)
        setattr(opt,k,v)
    for k,v in opt.__class__.__dict__.iteritems():
        if not k.startswith('__'):print(k,v)

    #vis.reinit(opt.env)
def write_csv(world,probability,csv_writer,patient_id,threshold=0.):
    '''
    @world:世界坐标，numpy （N，3）N为结点数目，坐标排序为X,Y,Z
    @probability：概率值，numpy（N,2），第一列为正概率
    @csv_writer：csv文件读写器
    @threshold：概率阈值，大于此阈值的概率才写到csv文件
    Return：None
    TODO：将样本的分类结果写入csv文件
    '''
    for j in range(world.shape[0]):
        if probability[j]>threshold:
            row=list(world[j])
            row.append(probability[j])
            row=[patient_id]+row
            # print row
            csv_writer.writerow(row)
    
def do_class(imgs,model):
    '''
    @img:待送入模型的图像，numpy（N,D,D,D）
    @model：用于分类的名
    Return：result，Numpy分类结果
    TODO：对检测到的结点进行二值分类
    '''
    
    length=imgs.shape[0]
    result=np.zeros([length])
    for j in range(length):
        img=imgs[j]
        img=torch.from_numpy(img[np.newaxis,np.newaxis,:,:,:])
        img=torch.autograd.Variable(img, volatile=True).float().cuda()
        batch_result=get_pro(model(img))
        result[j]=torch.nn.functional.softmax(batch_result).data.cpu().numpy()[0][1]
    return result

def get_pro(data):return data
    # p = 0 
    # for data_ in data:
    #     p+= t.nn.functional.softmax(data_)
    # return p/3.

    #!TODO:del this
def zero_normalize(image, mean=-600.0, var=-300.0):
    image = (image - mean) / (var)
    image[image > 1] = 1.
    image[image < 0] = 0.
    return image

def doTest(**kwargs):
    parse(kwargs)
    model1=Classifier1().cuda().eval()
    model1.load(opt.model_dir1)
    model2=Classifier2().cuda().eval()
    model2.load(opt.model_dir2)
    model3=Classifier3().cuda().eval()
    model3.load(opt.model_dir3)
    nodule_list=glob(opt.img_dir+'*_nodule.npy')
    center_list=glob(opt.img_dir+'*_center.npy')
    f=open(opt.csv_file, "wa")
    csv_writer = csv.writer(f, dialect="excel")
    csv_writer.writerow(
        ['seriesuid', 'coordX', 'coordY', 'coordZ', 'probability'])
    print nodule_list[:10]
    for i,patient in enumerate(nodule_list[:opt.limit]):
        if os.path.exists('/tmp/dcsb'):
            import ipdb
            ipdb.set_trace()
        patient_id=patient.split('/')[-1].split('_')[-2]
        #if int( patient_id.split('-')[1])<800:continue
        # print 'doing on',patient_id
        patient_center=get_filename(center_list,patient_id)
        imgs=np.load(patient)
        bb=normalize(imgs)#导入结点文件
        cc=zero_normalize(imgs)
        aa=np.load(patient_center)
        result1=do_class(bb[:,24-20:24+20,24-20:24+20,24-20:24+20],model1)
        result2=do_class(cc[:,24-10:24+10,24-18:24+18,24-18:24+18],model2)
        result3=do_class(bb[:,24-20:24+20,24-20:24+20,24-20:24+20],model3)
        result=(result1+result2+result3)/3.0
        length=aa.shape[0]
        print "length: ",length
        if length<opt.topN:
            topN=length
        else:
            topN=opt.topN	
        index=get_topn(result,topN)
        probability=result[index]
        center_=aa[index]
        world=voxel_2_world(center_[:,::-1],patient_id)
        write_csv(world,probability,csv_writer,patient_id,opt.prob_threshould)
        if i%20==0:
            print i," hava done" 



if __name__=='__main__':
    fire.Fire()
    

        
        
