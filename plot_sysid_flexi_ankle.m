clear; clc; close all;

% common_name='251108_Flexi_Ankle_R_ID_';
common_name='251108_Flexi_Ankle_L_ID_';

scriptDir = fileparts(mfilename('fullpath'));
fileList = dir(fullfile(scriptDir, [common_name '*']));
fileNames = string({fileList.name});
fileNames = extractBefore(fileNames, ".txt");


%%
for i=1:length(fileNames)
    if exist("Frequency_domain_"+fileNames(i),'file')
        disp("Frequency_domain_"+fileNames(i)+".txt")
    else
        do_sys_id_analysis_flexi_ankle(fileNames(i));
    end
end


%%
close all;
s= tf('s');
% kfn=1.157; ks=18.16; N1=6; Wf=0.12;
% keq_n=kfn*ks/(ks+N1^2*kfn)
% Weq=ks*Wf/(ks+N1^2*kfn*(1+Wf))
% Ji =0.00075718*5;Bi=0.0039754; Kt = 0.085*5*1.1;
% Jm = Ji*Kt*0.6; Bm = Bi*Kt*4;
% Pm = 1/(Jm*s^2+Bm*s);
% Kt=52.5*0.6*10^-3; ps=6*10^-3; Jm=0.007; Bm=0.004; kf=1.157*1.5;
Kt=52.5*1.0*10^-3; 
ps=6*10^-3; 
Jm=0.003; 
Bm=0.2; 
kf=0.275; %Nm/rad by experiment
eta=0.9;

Kp=0.9; Ki=0.0001; Kd=0;
% Kp=30; Ki=0.2; Kd=0;
C=Kp+Kd*s+Ki/s;

% Psys = Kt*2*3.14/ps*kf/(Jm*C*s^2+(C*Bm+1)*s+kf)
Psys = eta*2*pi/ps*kf*C*Kt/(Jm*s^2+(Bm+C*Kt)*s+kf)
Psys=minreal(Psys);

Psys2 = eta*Kt*2*pi/ps*kf/(Jm*s^2+Bm*s+kf)
% [ns,ds] = tfdata(Psys,'v');
% Psys2 = tf(ns(3)+ns(4),ds(1:3));
% 
[mag_tf_measured, phase_tf_measured, wout]=bode(minreal(Psys));
mag_nominal=mag_tf_measured(:);
phase_nominal=phase_tf_measured(:);

[mag_tf_measured2, phase_tf_measured2, wout2]=bode(minreal(Psys2));
mag_nominal2=mag_tf_measured2(:);
phase_nominal2=phase_tf_measured2(:);

data = cell(length(fileNames),1);
colors = [
    0 0.4470 0.7410;  % 파랑
    0.8500 0.3250 0.0980;  % 빨강
    0.4660 0.6740 0.1880;  % 초록
    0.4940 0.1840 0.5560;  % 보라
    0 0.4470 0.7410;  % 파랑
    0.8500 0.3250 0.0980;  % 빨강
    0.4660 0.6740 0.1880;  % 초록
    0.4940 0.1840 0.5560;  % 보라
];
for i=1:length(fileNames)
    filename = sprintf('Frequency_domain_%s.txt', fileNames(i));
    data{i} = load(filename);
    freq=data{i}(:,1);
    mag=data{i}(:,2);
    phase=data{i}(:,3);
    mag_lin=10.^(mag./20)

%     [mag_nom, phase_nom, nom]=bode(Psys,2*pi*freq);
%     mag_nom=squeeze(mag_nom);
% 
%     E=abs((mag_nom-mag_lin)./mag_nom);
    figure(1);
    subplot(2,1,1);
    semilogx(freq, mag, '.-','lineWidth',1.2,'Color',colors(i,:)); hold on;
    xlim([0.1 20]); xlabel('Frequency(Hz)'); ylabel('Magnitude(dB)');
    subplot(2,1,2);
    semilogx(freq, phase, '.-','lineWidth',1.2,'Color',colors(i,:)); hold on;
    xlim([0.1 20]); xlabel('Frequency(Hz)'); ylabel('Phase(deg)');
%     semilogx(wout/2/pi, phase_nominal);
%     figure(2);
%     semilogx(freq, 20*log10(abs(E.^-1)), '-','lineWidth',1.2); hold on;
end

fig1=figure(1); hold on;
subplot(2,1,1);
semilogx(wout/2/pi, 20*log10(mag_nominal),'k','LineWidth',1.5);
% semilogx(wout2/2/pi, 20*log10(mag_nominal2),'k','LineWidth',1.0); 
subplot(2,1,2);
semilogx(wout/2/pi, phase_nominal,'k','LineWidth',1.5);
semilogx(wout2/2/pi, phase_nominal2,'k','LineWidth',1.0);

% xlim([0.2 20]); ylim([-60 -5]); xlabel('Frequency(Hz)'); ylabel('Magnitude(dB)');
% legend('G.C 10%','G.C 40%','G.C 70%','Nominal model')
legend('1 rad/s','','2 rad/s','','3 rad/s')
set(fig1, 'OuterPosition', [3, 270, 800, 500]);
set(gca,"FontName",'Times New Roman', 'FontSize',12)
% % Qfilter
% z=tf('z',0.001);
% Qfilter=0.0037086/(z-0.9391)^2;
% [mag_Q, phase_Q, wout]=bode(Qfilter);
% mag_Q=squeeze(mag_Q);
% % %%%%%%%%%
% fig2=figure(2);
% semilogx(wout/2/pi, 20*log10(mag_Q),'k','LineWidth',1.5); 
% xlim([0.2 20]); ylim([-20 60]); xlabel('Frequency(Hz)'); ylabel('Magnitude(dB)');
% % legend('G.C 10%','G.C 40%','G.C 70%','Q filter')
% legend('1A','1.5A','2A','Q filter')
% set(fig2, 'OuterPosition', [3, 270, 800, 500]);
% set(gca,"FontName",'Times New Roman', 'FontSize',12)
%%
addpath("matlab\");

[ns,ds] = tfdata(Psys,'v');
ds/ns(3)
Psysd = c2d(Psys,0.001,'zoh');
[n,d] = tfdata(Psysd,'v');
Psysd2 = tf(n(2)+n(3),d,0.001);
dob(Psysd2, 20, [2 0]);
bode(Psysd2); hold on; bode(Psysd)
%%
Pptc=ptc(Psysd2)
function [mag, phase, wout]=bodeplot(dataname)
    data=load(dataname);
    
    y=data(:,1);
    yd=data(:,2);
    u=data(:,4);
    u_real=data(:,5);
    u_ref=data(:,6);
    t=(0:length(y)-1)*0.001;
%     d1 = designfilt("highpassiir",FilterOrder=12, ...
%     HalfPowerFrequency=0.000001,DesignMethod="butter");
%     yfilt = filtfilt(d1,y);
%     ydfilt=filtfilt(d1, yd);
    figure; subplot(2,1,1); plot(t, y, t, yd); subplot(2,1,2); plot(t, u);
    ts=0.001;
    id_data=iddata(y, yd, ts);
    tf_measured=spafdr(id_data);
    [mag_tf_measured, phase_tf_measured, wout]=bode(tf_measured);
    mag=mag_tf_measured(:);
    phase=phase_tf_measured(:);
end