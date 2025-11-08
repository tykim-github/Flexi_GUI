close all; clear all; clc;
filename = '20250307225949_PD_FF_DOB_LS_Kp0.2_Kd0.0001_T5_P55_R0.714_W60.txt';
data=importdata(filename, '\t', 1);  % 첫 번째 줄은 헤더로 읽어들임

% (3) 열 데이터를 변수로 분리
raw_data=data.data;
unique_rows = [true; diff(raw_data(:,1)) ~= 0];
filtered_data = raw_data(unique_rows, :);
cnt=filtered_data(:,1);
figure(101); plot(cnt);
ref=filtered_data(:,2);
force=filtered_data(:,3);
enc=filtered_data(:,4);
vel_ref=filtered_data(:,5);
dist=filtered_data(:,6);
FF=filtered_data(:,7);
FB=filtered_data(:,8);
gait_phase=filtered_data(:,9);

figure(1); hold on; plot(ref); plot(force);
figure(2); hold on; plot(vel_ref); plot(dist); plot(FF); plot(FB); legend("current","disturbance","FF","FB")
figure(3); plot(abs(ref-force)); yline(30);

disp(num2str(var(force)))
%%
filename = '20250306165456_noise_test_current_off.txt';
data=importdata(filename, '\t', 1);  % 첫 번째 줄은 헤더로 읽어들임

% (3) 열 데이터를 변수로 분리
raw_data=data.data;
unique_rows = [true; diff(raw_data(:,1)) ~= 0];
filtered_data = raw_data(unique_rows, :);
cnt=filtered_data(:,1);
figure(101); plot(cnt);
ref=filtered_data(:,2);
force=filtered_data(:,3);
enc=filtered_data(:,4);
vel_ref=filtered_data(:,5);
dist=filtered_data(:,6);
FF=filtered_data(:,7);
FB=filtered_data(:,8);
gait_phase=filtered_data(:,9);

figure(1); hold on; plot(vel_ref); plot(gait_phase);
figure(2); plot(force(13035:end),'k');
figure(3); plot(abs(ref-force)); yline(30);

disp(num2str(var(force(13035:end))))
%%
close all;
filename='20250313145439_PD_FF_DOB_LS_Fric_Kp0.2_Kd0.0001_T5_P55_R0.714_W60.txt';
data=importdata(filename, '\t', 1);  % 첫 번째 줄은 헤더로 읽어들임

% (3) 열 데이터를 변수로 분리
raw_data=data.data;
unique_rows = [true; diff(raw_data(:,1)) ~= 0];
filtered_data = raw_data(unique_rows, :);
cnt=filtered_data(:,1);
figure(101); plot(cnt);
torque_ref=filtered_data(:,2);
force=filtered_data(:,3);
enc=filtered_data(:,4);
cur=filtered_data(:,5);
vel_ref=filtered_data(:,6);
comp=filtered_data(:,7);
FB=filtered_data(:,8);
vel_act=filtered_data(:,9);
torque = filtered_data(:,10);


figure(1); plot(cnt); 
figure(2);  
subplot(3,1,1);
plot(vel_ref-FB); hold on; plot(vel_act); plot(-comp); legend('ref','actual','comp','dist')
subplot(3,1,2);
plot(force); hold on; plot(torque_ref);
subplot(3,1,3);
plot(enc);
vel_ankle = (enc-circshift(enc,1))*1000;
% figure(3);
% plot(vel_ankle);
figure(4); plot(cur);
figure(5); plot(torque);
figure(6); plot(torque./force*2*3.14/0.006);