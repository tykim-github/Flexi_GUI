clear; clc; close all;

set(groot,'defaulttextinterpreter','latex');  
set(groot, 'defaultAxesTickLabelInterpreter','latex');  
set(groot, 'defaultLegendInterpreter','latex');

%%

filename = 'sine_dob.txt'; range = 1364 : 22362;
T = readtable(filename);

% cnt ref_force force torque enc1 cur ref_vel mot_vel pmmg1 pmmg2
ylim([-22.5 22.5]);
cnt = 0.001*(T.Var1(range) - T.Var1(range(1)));
ref_force = T.Var2(range);
force = T.Var3(range);
torque = T.Var4(range);
enc1 = T.Var5(range);
cur = T.Var6(range);

figure('Position', [200 200 320 320]);
subplot(4,1,[1 2 3]);  grid on;
hold on
plot(cnt, ref_force, 'r');
plot(cnt, force, 'k');
xlim([0, inf]);
ylim([-22.5 22.5]);
ylabel('Force (N)')

subplot(4,1,4);
plot(cnt, ref_force - force, 'k');
xlim([0, inf]);
xlabel('Time (sec)');
ylabel('Error (N)');
grid on;

%%

filename = 'sine_pd.txt'; range = 1 : 22362;
T = readtable(filename);

% cnt ref_force force torque enc1 cur ref_vel mot_vel pmmg1 pmmg2

cnt = 0.001*(T.Var1(range) - T.Var1(range(1)));
ref_force = T.Var2(range);
force = T.Var3(range);
torque = T.Var4(range);
enc1 = T.Var5(range);
cur = T.Var6(range);

figure('Position', [200 200 320 320]);
subplot(4,1,[1 2 3]);  grid on;
hold on
plot(cnt, ref_force, 'r');
plot(cnt, force, 'k');
xlim([0, inf]);
ylim([-22.5 22.5]);
ylabel('Force (N)')

subplot(4,1,4);
plot(cnt, ref_force - force, 'k');
xlim([0, inf]);
xlabel('Time (sec)');
ylabel('Error (N)');
grid on;

%%

filename = 'square_dob.txt'; range = 1 : 16500;
T = readtable(filename);

% cnt ref_force force torque enc1 cur ref_vel mot_vel pmmg1 pmmg2

cnt = 0.001*(T.Var1(range) - T.Var1(range(1)));
ref_force = T.Var2(range);
force = T.Var3(range);
torque = T.Var4(range);
enc1 = T.Var5(range);
cur = T.Var6(range);

figure('Position', [200 200 320 320]);
subplot(4,1,[1 2 3]);  grid on;
hold on
plot(cnt, ref_force, 'r');
plot(cnt, force, 'k');
xlim([0, inf]);
ylim([-22.5 22.5]);
ylabel('Force (N)')

subplot(4,1,4);
plot(cnt, ref_force - force, 'k');
xlim([0, inf]);
xlabel('Time (sec)');
ylabel('Error (N)');
grid on;

%%

filename = 'square_pd.txt'; range = 1 : 16500;
T = readtable(filename);

% cnt ref_force force torque enc1 cur ref_vel mot_vel pmmg1 pmmg2

cnt = 0.001*(T.Var1(range) - T.Var1(range(1)));
ref_force = T.Var2(range);
force = T.Var3(range);
torque = T.Var4(range);
enc1 = T.Var5(range);
cur = T.Var6(range);

figure('Position', [200 200 320 320]);
subplot(4,1,[1 2 3]);  grid on;
hold on
plot(cnt, ref_force, 'r');
plot(cnt, force, 'k');
xlim([0, inf]);
ylim([-22.5 22.5]);
ylabel('Force (N)')

subplot(4,1,4);
plot(cnt, ref_force - force, 'k');
xlim([0, inf]);
xlabel('Time (sec)');
ylabel('Error (N)');
grid on;