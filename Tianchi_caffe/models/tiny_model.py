#encoding:utf-8
import caffe
import numpy as np
from caffe import layers as L
from caffe import params as P
from config import opt



def conv_bn(data,num_output,kernel_size=3,stride=1,padding=1,is_train=True):
    '''
    3D卷积+BatchNorm+Relu
    @data：待卷积数据
    @num_output：输出通道
    @kernel_size：卷积核大小
    @stride:步长
    @padding:填充
    Return：Relu激活后的结果
    '''
    conv=L.Convolution(data, kernel_size=kernel_size,stride=stride,pad=padding,
                            num_output=num_output,weight_filler=dict(type='xavier'))
    if is_train:
        kwargs={'engine':1}
    else:
        kwargs={'engine':1,'use_global_stats':True}
    conv=L.BatchNorm(conv,**kwargs)
    conv=L.Scale(conv,bias_term=True)
    
    return conv

def SingleConv(data,num_output,kernel_size=3,stride=1,padding=1,is_train=True):
    '''
    3D卷积+BatchNorm+Relu
    @data：待卷积数据
    @num_output：输出通道
    @kernel_size：卷积核大小
    @stride:步长
    @padding:填充
    Return：Relu激活后的结果
    '''
    conv=L.Convolution(data, kernel_size=kernel_size,stride=stride,pad=padding,
                            num_output=num_output,weight_filler=dict(type='xavier'))
    if is_train:
        kwargs={'engine':1}
    else:
        kwargs={'engine':1,'use_global_stats':True}
    conv=L.BatchNorm(conv,**kwargs)
    conv=L.Scale(conv,bias_term=True)
    conv=L.ReLU(conv,engine=3)
    return conv

 
def ResDown(data,cout):    
    # left_=SingleConv(data,cout,kernel_size=3,stride=2,padding=1)
    right = SingleConv(data,cout,kernel_size=3,stride=1,padding=1)    
    right = conv_bn(right,cout,kernel_size=3,stride=1,padding=1)
    data = conv_bn(data,cout,kernel_size=3,stride=2,padding=1)
    # data =  L.Pooling(data, kernel_size=3,stride=2,pad=1, pool=P.Pooling.AVE)
    return L.ReLU(L.Eltwise(data,right,operation=1,engine=3))

def ResBlock(data,cout,transform = False,z=False):
    # left_=SingleConv(data,cout,kernel_size=3,stride=2,padding=1)

    z_kernel_size,z_padding = (1,0) if z else (3,1)
    right = SingleConv(data,cout,kernel_size=[z_kernel_size,3,3],padding=[z_padding,1,1])
    right=conv_bn(right,cout,kernel_size=3,stride=1,padding=1)
    
    if transform:
        data = SingleConv(data,cout)
    return L.ReLU(L.Eltwise(data,right,operation=1,engine=3))


def bn(input,is_train):
    if is_train:
        kwargs={'engine':1}
    else:
        kwargs={'engine':1,'use_global_stats':True}
    return L.Scale(L.BatchNorm(input,**kwargs),bias_term=True)

class MutltiCNN(object):
    def __init__(self,model_name="tiny_cls",is_train=True):
        '''
        @model_def:模型定义.prototext文件路径
        @model_weight:已保存模型参数.caffemodel文件路径
        @model_name:模型名
        '''
        self.model_name=model_name
        self.is_train=is_train
        self.model_def="prototxt/tiny_cls.prototxt"
    def define_model(self):
        n = caffe.NetSpec()
        pylayer = 'ClsDataLayer'

        pydata_params = dict(phase='train', data_root=opt.cls_data_root,
                         batch_size=16,ratio=5,augument=True)
        n.data,_,_,n.label = L.Python(module='data.ClsDataLayer', layer=pylayer,
            ntop=4, param_str=str(pydata_params))

        n.pre_conv=SingleConv(n.data,64,kernel_size=1,stride=1,padding=0)
        
        n.res = ResBlock(n.pre_conv,64)
        n.res = ResDown(n.res,256)
        n.res = ResBlock(n.res,256)
        n.res = ResDown(n.res,1024)
        n.res = ResBlock(n.res,1024)
        n.res = ResBlock(n.res,1024)

        n.cls=L.Pooling(n.res, kernel_size=16,stride=1,pad=0, pool=P.Pooling.MAX)
        n.cls=L.InnerProduct(n.cls, num_output=2,weight_filler=dict(type='xavier'))
        
        n.loss=L.SoftmaxWithLoss(n.cls, n.label)

        with open(self.model_def, 'w') as f:
            f.write(str(n.to_proto()))
if __name__=="__main__":
    seg=MutltiCNN(is_train=True)
    seg.define_model()
        
        
        
        
        
        
        
        
        