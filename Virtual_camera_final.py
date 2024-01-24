
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import math

def camera(resolutionX, resolutionY, px_size, quantum_efficiency):
    return resolutionX, resolutionY, px_size, quantum_efficiency

def number_of_electrons(px_size,exposure_time,wavelength,irradiance,quantum_efficiency):
    number_of_photons = 50.34 * px_size *px_size * exposure_time / 1000 * wavelength * irradiance
    number_of_electrons=number_of_photons * quantum_efficiency

    return number_of_electrons

def noise(px_size,exposure_time,wavelength,irradiance,quantum_efficiency,PRNU,DSNU,dark_current,temporal_noise,sat_capacity,bit_depth,gain_factor):
    #noise variance can be added.
    shot_noise = number_of_electrons(px_size,exposure_time,wavelength,irradiance,quantum_efficiency)
    #qe*up
    PRNU_var = PRNU ** 2 * (shot_noise**2)
    DSNU_var = DSNU ** 2
    Dark_current_var = temporal_noise**2 + dark_current*exposure_time/(10**6)
    total_noise_var = shot_noise + PRNU_var +DSNU_var+ Dark_current_var
    noise_DN_volt = (total_noise_var)**0.5/sat_capacity *gain_factor
    #EMVA1288 3.1 (45)
    bins =  2 ** bit_depth - 1
    if noise_DN_volt > 1:
        noise_DN_volt=1
        noise_DN_sigma = 0
    else:
        noise_DN_sigma = noise_DN_volt * bins

    return noise_DN_sigma



def total_electons(irradiance, exposure_time, gain_factor,quantum_efficiency,px_size,wavelength):
    resolutionX, resolutionY, px_size, quantum_efficiency = camera(500, 500, px_size, quantum_efficiency)
    # distributed photons described by poisson dis.
    electron_number = number_of_electrons(px_size, exposure_time, wavelength, irradiance, quantum_efficiency)

    total_electrons = electron_number * gain_factor

    return total_electrons

def gray_value(bit_depth,sat_capacity,light_int,exposure_time,gain_factor,quantum_efficiency,px_size,wavelength,dark_current):
    bins = 2 ** bit_depth - 1
    voltage = total_electons(light_int,exposure_time,gain_factor,quantum_efficiency,px_size,wavelength) / sat_capacity

    if voltage> 1:
        voltage =1
        GV = bins
    else:
        GV = np.floor(voltage * bins + dark_current * exposure_time/(10**6))

    return GV



def get_data():

    if sensor.get() == 'manual':
        px_size = float(pxsize_entry.get())
        sat_capacity = int(sat_entry.get())
        irradiance = float(irradiance_entry.get())
        light_int = irradiance
        wavelength = float(wavelength_entry.get())
        quantum_efficiency = float(QE_entry.get())
        exposure_time = int(exp_entry.get())
        gain_factor = float(gain_entry.get())
        PRNU = float(PRNU_entry.get())/100
        DSNU = float(DSNU_entry.get())
        dark_current = float(dark_current_entry.get())
        temporal_noise = float(temporal_noise_entry.get())
        bit_depth = bit_depth_entry.get()
    else:
        df = pd.read_excel('sensor.xlsx')
        px_size = df[sensor.get()][0]
        sat_capacity = df[sensor.get()][1]
        wavelength = df[sensor.get()][2]
        quantum_efficiency = df[sensor.get()][3]
        PRNU = df[sensor.get()][4]/100
        DSNU = df[sensor.get()][5]
        dark_current = df[sensor.get()][6]
        temporal_noise = df[sensor.get()][7]
        irradiance = float(irradiance_entry.get())
        light_int = irradiance
        exposure_time = int(exp_entry.get())
        gain_factor = float(gain_entry.get())
        bit_depth = bit_depth_entry.get()




    if bit_depth =='12bit':
        bit_depth = 12
        GV_mean = gray_value(bit_depth,sat_capacity,light_int,exposure_time,gain_factor,quantum_efficiency,px_size,wavelength,dark_current)
        GV_8bit = GV_mean / 16
        noise_12bit = noise(px_size,exposure_time,wavelength,irradiance,quantum_efficiency,PRNU,DSNU,dark_current,temporal_noise,sat_capacity,bit_depth,gain_factor)
        noise_8bit = noise_12bit / 16
        img = (np.random.normal(loc=GV_8bit, scale=noise_8bit, size=(500, 500)))
    if bit_depth =='14bit':
        bit_depth = 14
        GV_mean = gray_value(bit_depth,sat_capacity,light_int,exposure_time,gain_factor,quantum_efficiency,px_size,wavelength,dark_current)
        GV_8bit = GV_mean / 64
        noise_12bit = noise(px_size,exposure_time,wavelength,irradiance,quantum_efficiency,PRNU,DSNU,dark_current,temporal_noise,sat_capacity,bit_depth,gain_factor)
        noise_8bit = noise_12bit / 64
        img = (np.random.normal(loc=GV_8bit, scale=noise_8bit, size=(500, 500)))
    if bit_depth =='10bit':
        bit_depth = 10
        GV_mean = gray_value(bit_depth,sat_capacity,light_int,exposure_time,gain_factor,quantum_efficiency,px_size,wavelength,dark_current)
        GV_8bit = GV_mean / 4
        noise_12bit = noise(px_size,exposure_time,wavelength,irradiance,quantum_efficiency,PRNU,DSNU,dark_current,temporal_noise,sat_capacity,bit_depth,gain_factor)
        noise_8bit = noise_12bit / 4
        img = (np.random.normal(loc=GV_8bit, scale=noise_8bit, size=(500, 500)))
    else:
        bit_depth = 8
        GV_mean = gray_value(bit_depth,sat_capacity,light_int,exposure_time,gain_factor,quantum_efficiency,px_size,wavelength,dark_current)
        GV_8bit = GV_mean
        noise_12bit = noise(px_size,exposure_time,wavelength,irradiance,quantum_efficiency,PRNU,DSNU,dark_current,temporal_noise,sat_capacity,bit_depth,gain_factor)
        noise_8bit = noise_12bit
        img = (np.random.normal(loc=GV_8bit, scale=noise_8bit, size=(500, 500)))



    factor = int(bin_entry.get())
    im_size_orig = img.shape
    im_reshape = img.reshape(im_size_orig[0]//factor, factor, im_size_orig[1]//factor, factor)
    if bin_method_entry.get() == 'sum':
        img = im_reshape.sum(-1).sum(1)
    else:
        img = im_reshape.mean(-1).mean(1)

    img[img>255] = 255

    fig = plt.figure(figsize=(5.5, 4))
    plt.hist(img.ravel(), 256, [0, 256],density=True)
    plt.xlabel("Gray Value[DN]")
    plt.ylabel("number of pixels[%]")
    plt.xlim(0,255)
    plt.draw()

    canvas = FigureCanvasTkAgg(fig, master=tab3)
    canvas.draw()
    canvas._tkcanvas.grid(column=0, row=10)

    im = Image.fromarray(img)
    im.show()
    u = np.mean(im)
    s = np.std(im)

    if s == 0:
        SNR = 'inf'
        result = 'Mean GV : {:.2f} [DN] , σ : {:.2f} [DN], SNR : inf'.format(u, s)
    else:
        SNR = u/s
        result = 'Mean GV : {:.2f} [DN] , σ : {:.2f} [DN] , SNR : {:.2f} ({:.2f} dB)'.format(u,s,SNR,20*math.log(SNR,10))
    result_label.configure(text=result)
    result_label_2.configure(text=result)

    Nyquist = 1 / 2 / float(pxsize_entry.get()) * 1000 / float(bin_entry.get())
    Nyquist_result = 'Nyquist frequency : {:.2f} [lp/mm]'.format(Nyquist)
    Nyquist_label.configure(text=Nyquist_result)

def update():

    sensorname = sensor.get()
    if sensor.get() != 'manual':
        df = pd.read_excel('sensor.xlsx')
        pxsize_entry.delete(0,"end")
        pxsize_entry.insert(0, df[sensor.get()][0])
        sat_entry.delete(0,"end")
        sat_entry.insert(0, int(df[sensor.get()][1]))
        wavelength_entry.delete(0,'end')
        wavelength_entry.insert(0,df[sensor.get()][2])
        QE_entry.delete(0,'end')
        QE_entry.insert(0,df[sensor.get()][3])
        PRNU_entry.delete(0,'end')
        PRNU_entry.insert(0,df[sensor.get()][4])
        DSNU_entry.delete(0,'end')
        DSNU_entry.insert(0,df[sensor.get()][5])
        dark_current_entry.delete(0,'end')
        dark_current_entry.insert(0,df[sensor.get()][6])
        temporal_noise_entry.delete(0,'end')
        temporal_noise_entry.insert(0,df[sensor.get()][7])

        df = pd.read_excel('sensor.xlsx')
        sensor_H_entry.delete(0,'end')
        sensor_H_entry.insert(0,round(df[sensor.get()][8],2))
        sensor_V_entry.delete(0, 'end')
        sensor_V_entry.insert(0, round(df[sensor.get()][9],2))
        COC_entry.delete(0,'end')
        COC_entry.insert(0, round(df[sensor.get()][10]/1730,3))


def lens():

    f = float(FL_entry.get())
    p = float(WD_entry.get())
    q = f*p / (p-f)
    M = p/q


    df = pd.read_excel('sensor.xlsx')
    FOV_H = round(df[sensor.get()][8] *M,1)
    FOV_V = round(df[sensor.get()][9] *M,1)
    AOV_H = 2 * math.atan(df[sensor.get()][8]/f/2) * 180 /3.1415926
    AOV_V = 2 * math.atan(df[sensor.get()][9]/f/2) * 180 /3.1415926


    fov_H_entry.delete(0, 'end')
    fov_H_entry.insert(0, round(FOV_H,2))
    fov_V_entry.delete(0, 'end')
    fov_V_entry.insert(0, round(FOV_V,2))
    aov_H_entry.delete(0, 'end')
    aov_H_entry.insert(0, round(AOV_H,2))
    aov_V_entry.delete(0, 'end')
    aov_V_entry.insert(0, round(AOV_V,2))



def DOF_cal():

    try:
        df = pd.read_excel('sensor.xlsx')
        f = float(FL_entry.get())
        p = float(WD_entry.get())
        q = f * p / (p - f)
        M = p / q
        A = float(f_entry.get()[1:])
        A_eq = (1+1/M)*A
        C = df[sensor.get()][10]/1730

        DOF = 2 * A_eq *C *p**2*f**2/(f**4 - (A_eq**2)*(C**2)*(p**2))

        DOF_entry.delete(0,'end')
        DOF_entry.insert(0,round(DOF,2))
        M_entry.delete(0,'end')
        M_entry.insert(0,round(M,2))

        err = ''
        err_label.configure(text=err)

    except:
        err = 'You have not selected a sensor yet or some parameters are missing.'
        err_label.configure(text=err)



win = tk.Tk()
win.title('Virtual camera') # 更改視窗的標題
win.geometry('500x500')  # 修改視窗大小(寬x高)
win.resizable(True, True) # 如果不想讓使用者能調整視窗大小的話就均設為False
win.iconbitmap('basler_icon.ico') # 更改左上角的icon圖示

# https://blog.techbridge.cc/2019/09/21/how-to-use-python-tkinter-to-make-gui-app-tutorial/
tabControl = ttk.Notebook(win)          # Create Tab Control

tab1 = ttk.Frame(tabControl)            # Create a tab
tabControl.add(tab1, text='Basic setting')      # Add the tab
tab2 = ttk.Frame(tabControl)            # Add a second tab
tabControl.add(tab2, text='Advance setting')
tabControl.pack(expand=1, fill="both")  # Pack to make visible
tab3 = ttk.Frame(tabControl)            # Add a second tab
tabControl.add(tab3, text='Stats.')
tabControl.pack(expand=1, fill="both")
tab4 = ttk.Frame(tabControl)            # Add a second tab
tabControl.add(tab4, text='Field of View')
tabControl.pack(expand=1, fill="both")
tab5 = ttk.Frame(tabControl)            # Add a second tab
tabControl.add(tab5, text='Depth of Field')
tabControl.pack(expand=1, fill="both")
tab6 = ttk.Frame(tabControl)            # Add a second tab
tabControl.add(tab6, text='help')
tabControl.pack(expand=1, fill="both")




logo=Image.open('logo_basler.png')
logo=ImageTk.PhotoImage(logo.resize((100, 50)))
logoLabel=tk.Label(win,image=logo)
logoLabel.pack(anchor='s',fill='y')





header_label = tk.Label(tab1, text='Sensor simulator',font = ('microsoft yahei',12,'bold'),foreground ='#484891')
header_label.pack(anchor='n',fill='y')
sensor = ttk.Combobox(tab1,values=['manual','IMX174','IMX178','IMX183','IMX226','IMX249','IMX250','IMX252','IMX253','IMX255','IMX264','IMX265','IMX267'
,'IMX273','IMX287','IMX304','IMX334','IMX392','IMX540','IMX541','IMX542','IMX545','IMX546','IMX547','CMV2000','CMV4000','PYTHON 1300','MT9P031'
],width=10)
sensor.current(0)
sensor.pack()


px_size = tk.StringVar(None, '3.45')
pxsize_label = tk.Label(tab1, text="px size[um]:")
pxsize_label.pack()
pxsize_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=px_size,width=10)
pxsize_entry.pack()



sat_capacity = tk.StringVar(None, '10000')
sat_label = tk.Label(tab1, text="sat. capacity[e]:")
sat_label.pack()
sat_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=sat_capacity,width=10)
sat_entry.pack()



wavelength = tk.StringVar(None, '0.545')
wavelength_label = tk.Label(tab1, text="wavelength [um]:")
wavelength_label.pack()
wavelength_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=wavelength,width=10)
wavelength_entry.pack()
# #


QE = tk.StringVar(None, '0.66')
QE_label = tk.Label(tab1, text="Quantum efficiency [0-1]:")
QE_label.pack()
QE_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=QE,width=10)
QE_entry.pack()

irradiance = tk.StringVar(None, '5')
irradiance_label = tk.Label(tab1, text="irradiance [uW/cm^2]:")
irradiance_label.pack()
irradiance_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=irradiance,width=10)
irradiance_entry.pack()


exp = tk.StringVar(None, '5000')
exp_label = tk.Label(tab1, text="exp. time [us]:")
exp_label.pack()
exp_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=exp,width=10)
exp_entry.pack()


gain = tk.StringVar(None, '1')
gain_label = tk.Label(tab1, text="gain factor :")
gain_label.pack()
gain_entry = tk.Entry(tab1, foreground="#0080FF", textvariable=gain,width=10)
gain_entry.pack()


bit_depth_Label= tk.Label(tab2,text = "bit depth of raw data").pack()
bit_depth_entry = ttk.Combobox(tab2,  values=['14bit','12bit','10bit','8bit'],width=5)
bit_depth_entry.pack()
bit_depth_entry.current(1)


temporal_noise = tk.StringVar(None, '2')
temporal_noise_label = tk.Label(tab2, text="temporal noise [e] :")
temporal_noise_label.pack()
temporal_noise_entry = tk.Entry(tab2, foreground="#0080FF", textvariable=temporal_noise,width=5)
temporal_noise_entry.pack()

dark_current = tk.StringVar(None, '0.5')
dark_current_label = tk.Label(tab2, text="dark current [e/s] :")
dark_current_label.pack()
dark_current_entry = tk.Entry(tab2, foreground="#0080FF", textvariable=dark_current,width=5)
dark_current_entry.pack()

PRNU = tk.StringVar(None, '0.5')
PRNU_label = tk.Label(tab2, text="PRNU [%] :")
PRNU_label.pack()
PRNU_entry = tk.Entry(tab2, foreground="#0080FF", textvariable=PRNU,width=5)
PRNU_entry.pack()

DSNU = tk.StringVar(None, '1')
DSNU_label = tk.Label(tab2, text="DSNU [e] :")
DSNU_label.pack()
DSNU_entry = tk.Entry(tab2, foreground="#0080FF", textvariable=DSNU,width=5)
DSNU_entry.pack()


bin = tk.StringVar(None, '1')
bin_label = tk.Label(tab2, text="bin factor :")
bin_label.pack()
bin_entry = ttk.Combobox(tab2,  values=['1','2','4'],width=3)
bin_entry.pack()
bin_entry.current(0)

bin_method = tk.StringVar(None, 'sum')
bin_method_label = tk.Label(tab2, text="bin method :")
bin_method_label.pack()
bin_method_entry = ttk.Combobox(tab2,  values=['sum','average'],width=8)
bin_method_entry.pack()
bin_method_entry.current(0)


sensor_H = tk.StringVar(None)
sensor_V_label = tk.Label(tab4,text='sensor horizontal view[mm]').pack()
sensor_H_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=sensor_H,width=5)
sensor_H_entry.pack()

sensor_V = tk.StringVar(None)
sensor_V_label = tk.Label(tab4,text='sensor vertical view[mm]').pack()
sensor_V_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=sensor_V,width=5)
sensor_V_entry.pack()

WD = tk.StringVar(None,100)
WD_label = tk.Label(tab4,text='Working distance[mm]').pack()
WD_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=WD,width=5)
WD_entry.pack()

FL = tk.StringVar(None,16)
FL_label = tk.Label(tab4,text='Focal length[mm]').pack()
FL_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=FL,width=5)
FL_entry.pack()

fov_H = tk.StringVar(None)
fov_H_label = tk.Label(tab4,text='horizontal view[mm]').pack()
fov_H_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=fov_H,width=5)
fov_H_entry.pack()
fov_V = tk.StringVar(None)
fov_V_label = tk.Label(tab4,text='Vertical view[mm]').pack()
fov_V_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=fov_V,width=5)
fov_V_entry.pack()

aov_H = tk.StringVar(None)
aov_H_label = tk.Label(tab4,text='Angle of horizontal view[°]').pack()
aov_H_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=aov_H,width=5)
aov_H_entry.pack()
aov_V = tk.StringVar(None)
aov_V_label = tk.Label(tab4,text='Angle of Vertical view[°]').pack()
aov_V_entry = tk.Entry(tab4, foreground="#0080FF", textvariable=aov_V,width=5)
aov_V_entry.pack()


f_V = tk.StringVar(None)
f_label = tk.Label(tab5,text='Aperture').pack()
f_entry = ttk.Combobox(tab5,values=['f0.95','f1.2','f1.4','f1.8','f2.0','f2.8','f3.5','f4.0','f5.6','f6.3','f8.0','f11','f13','f16','f22'
],width=5)
f_entry.pack()
WD = tk.StringVar(None,200)
WD_label = tk.Label(tab5,text='Working distance[mm]').pack()
WD_entry = tk.Entry(tab5, foreground="#0080FF", textvariable=WD,width=5)
WD_entry.pack()
FL = tk.StringVar(None,16)
FL_label = tk.Label(tab5,text='Focal length[mm]').pack()
FL_entry = tk.Entry(tab5, foreground="#0080FF", textvariable=FL,width=5)
FL_entry.pack()
M = tk.StringVar(None)
M_label = tk.Label(tab5,text='Magnification').pack()
M_entry = tk.Entry(tab5, foreground="#0080FF", textvariable=M,width=5)
M_entry.pack()
COC = tk.StringVar(None)
COC_label = tk.Label(tab5,text='Circle of Confusion (CoC)[mm]').pack()
COC_entry = tk.Entry(tab5, foreground="#0080FF", textvariable=COC,width=8)
COC_entry.pack()
DOF = tk.StringVar(None)
DOF_label = tk.Label(tab5,text='Depth of field [mm]').pack()
DOF_entry = tk.Entry(tab5, foreground="#0080FF", textvariable=DOF,width=8)
DOF_entry.pack()

help_label_0 = tk.Label(tab6,text='').pack(anchor='nw')
help_label_1 = tk.Label(tab6,text='※All data of cameras are measuremed by Basler AG.',foreground='#0066CC').pack(anchor='nw')
help_label_1 = tk.Label(tab6,text='※If dark current of sensor is not measured, this project used 0.5e/s as basic parameter.',foreground='#0066CC').pack(anchor='nw')
help_label_2 = tk.Label(tab6,text='※Camera calculation theory based on EMVA release 3.1.',foreground='#0066CC').pack(anchor='nw')
EMVA=Image.open('EMVA.JPG')
EMVA=ImageTk.PhotoImage(EMVA.resize((500,200 )))
EMVALabel=tk.Label(tab6,image=EMVA)
EMVALabel.pack(anchor='s',fill='y')
help_label_3 = tk.Label(tab6,text='※COC estimated by Zeiss formula.',foreground='#0066CC').pack(anchor='nw')
help_label_4 = tk.Label(tab6,text='※If you have any suggestions, pls contact :',foreground='#0066CC').pack(anchor='nw')
Email =tk.StringVar(None,'Enso.tseng@baslerweb.com')
Email.entry = tk.Entry(tab6, foreground="#0072E3", textvariable=Email,width=25)
Email.entry.pack(anchor='nw')



# 設定 Button

button_update = tk.Button(tab1, text="updating parameters", command = update,activebackground = '#0066CC',activeforeground = "#F75000")
button_update.pack()
button_update = tk.Button(tab4, text="updating parameters", command = update,activebackground = '#0066CC',activeforeground = "#F75000")
button_update.pack()
button = tk.Button(tab1, text="Create a picture", command = get_data,activebackground = '#0066CC',activeforeground = "#F75000")
button.pack()
button = tk.Button(tab4, text="FOV calculation", command = lens,activebackground = '#0066CC',activeforeground = "#F75000")
button.pack()
button_update = tk.Button(tab5, text="updating parameters", command = update,activebackground = '#0066CC',activeforeground = "#F75000")
button_update.pack()
button = tk.Button(tab5, text="DOF calculation", command = DOF_cal,activebackground = '#0066CC',activeforeground = "#F75000")
button.pack()

result_FOV_label = tk.Label(tab4)
result_FOV_label.pack()
result_AOV_label = tk.Label(tab4)
result_AOV_label.pack()
result_label = tk.Label(tab1)
result_label.pack()
Nyquist_label = tk.Label(tab1)
Nyquist_label.pack()
result_label_2 = tk.Label(tab3)
result_label_2.grid()
err_label = tk.Label(tab5)
err_label.pack()




win.mainloop()



