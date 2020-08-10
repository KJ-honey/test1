import os
import sys
from configparser import ConfigParser

def main():    

    config=ConfigParser(allow_no_value=True)
    config.read('config.ini',encoding='utf-8')
    config=config['Paths']
    Path_csv=config['Path_csv']
    Path_ISO=config['Path_ISO']

    
    start=input('%s 파일에 직접 데이터를 덮어씌웁니다. 진행하시겠습니까? (y/n)'%Path_ISO)
    if start=='y' or start=='Y' or start=='yes' or start=='Yes'or start=='YES': 
        print('대사 입력을 시작합니다. 이 작업은 몇십초 소요될 수 있습니다.')
    else :
        print("프로그램을 종료하겠습니다.")
        os.system('Pause')
        exit()
    script(Path_csv,Path_ISO)
    print("완료됐습니다.")
    os.system('Pause')
    exit()

def script(csvpath,iso):
    isof=open(iso,'rb')
    isof.seek(379666432)
    data=isof.read(2034592)		#스크립트 전체 덤프
    isof.close()
    
    filename='textBinBecomeDelete.bin'
    textpath='textDumpBecomeDelete.txt'
    #csvpath='test.csv'

    inf=open(filename,'wb+')
    textf=open(textpath,'w+',encoding='utf-16')
    csv=open(csvpath,'r',encoding='utf-8')

    inf.write(data)
    textf.write(csv.read())
    csv.close()
    textf.seek(0)

    headerList=find_header(b'\x45\x54\x44\x46',data)
    dialogNum=dialog_num(headerList,data)
    texts=find_dialog(textf)
    textf.close()

    script_import(headerList,dialogNum,texts,inf)

    inf.seek(0)
    data=inf.read()
    inf.close()
    os.remove(filename)
    os.remove(textpath)


    isof=open(iso,'rb+')
    isof.seek(379666432)
    isof.write(data)
    isof.close()


def find_dialog(textf):
    retlist=[]
    lines=textf.readlines()
    sw=0
    for line in lines:
        which=line.find(",")
        which2=line[which+1:].find(",")
        which3=line[which+1+which2+1:].find(",")
        line=line[which+which2+2:which+which2+2+which3]
        line=line.replace('"',"")

        retlist.append(line)
    return retlist

def dialog_num(headerList,data):
    dialogOffset=[]
    for i in headerList:
        dialogOffset.append(int.from_bytes(data[i+12:i+14],byteorder='little'))
    return dialogOffset

def find_header(find_str,data):
    count=0
    findOffset=[]
    where=data.find(find_str)
    findOffset.append(where)
    count+=1
    while True:
        where=data[findOffset[count-1]+4:].find(find_str)
        if where==-1 :
            break
        findOffset.append(where+4+findOffset[count-1])
        count+=1
    return findOffset

def str_to_bin(string_,sw):
    tbl=open('tbl.tbl','r',encoding='utf-16')
    kor=tbl.readline()
    jpn=tbl.readline()
    while True:
        try:
            if sw==1:                                               # Str to Bin : 입력기에서 사용
                string_=string_.translate(str.maketrans(kor+'&①②③~',jpn+'＆１２３≒'))
                string_=bytes(string_,'shift-jis',errors='replace')
                string_=string_.replace(b'\x81\x95',b'\xff\x80')
                string_=string_.replace(b'\x81\xE0',b'\x81\x60')
                return string_
            elif sw==2:                                             # Bin to Str : 출력기에서 사용
                string_=string_.replace(b'\xFF\x80',b'\x81\x95')    # 개행을 전각&으로 출력
                string_=string_.replace(b'\xFF\x44',b'\x81\x83')    # 이하 < or >
                string_=string_.replace(b'\xFF\x42',b'\x81\x83')
                string_=string_.replace(b'\xFF\x40',b'\x81\x84')
                string_=string_.replace(b'\xFF\x00',b'\x81\x84')
                string_=str(string_,encoding='shift-jis')
                string_=string_.translate(str.maketrans(jpn,kor))
                return string_
        except UnicodeDecodeError or LookupError:
            outerrlog=open('errLog.log','rb+')
            print(string_)
            outerrlog.write(string_)
            outerrlog.close()
            exit()

def script_import(headerList,dialogNum,texts,inf):
    count=0
    finishOffset=0
    for h,d in zip(headerList,dialogNum):
        if inf.tell()==0:
            pass
        else:
            ETDFOffset=h
            num=ETDFOffset-finishOffset
            data=inf.read(num)
            pBinOffset=data.find(b'\x70\x42\x69\x6E')
            inf.seek(finishOffset)
            hex00appender(pBinOffset,inf)
        #Currentdata=data[h:]
        inf.seek(h)
        #print('Go to ETDF Offset')
        #print(inf.tell())
        inf.seek(8,1)
        strangenum=inf.read(2)
        strangenum=int.from_bytes(bytes=strangenum,byteorder='little')

        #Currentdata=Currentdata[strangenum*16+8:]
        inf.seek(strangenum*16+6,1)
        lengths=0
        #print('Go to dialogs length Offset')
        #print(inf.tell())
        inf.seek(36,1)
        for i in range(d): # 텍스트에서 대사들 읽어서 길이 계산후 파일에 오프셋 입력하는 루프
            if i == 0: 
                firstOffset=int.from_bytes(bytes=inf.read(2),byteorder='little')
                #print(hex(firstOffset))
            else: 
                writeOffset=lengths
                inf.write(int.to_bytes(writeOffset,2,'little'))

            while True:
                try:
                    text=texts[count+i]
                    text=str_to_bin(text,1)
                    break
                except LookupError or IndexError:
                    print('i = %d, d= %d, Offset= %s, text= %s'%(i,d,inf.tell(),texts[count+i-1]))
                    exit()
            length=len(text)
            if i==0:lengths=firstOffset+length+1
            else:lengths+=length+1
            inf.seek(30,1)
        
        inf.seek(-20,1)
        #print('Go to dialogs Offset')
        #print(inf.tell())
        for i in range(d): # 파일에 순서대로 파일 나열 입력
            text=texts[count+i]
            while True:
                try:
                    text=str_to_bin(text,1)
                    break
                except LookupError:
                    print(inf.tell())
                    print(text)
                    exit()
            inf.write(text)
            #print(inf.read(10))
            inf.write(b'\x00')
        finishOffset=inf.tell()
        count+=d
def hex00appender(num,outf):
    ff=b'\x00' # 추가 할 값
    i=0
    while i<num :
        outf.write(ff)
        i+=1
if __name__ == "__main__":
    main()