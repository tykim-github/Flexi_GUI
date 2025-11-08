clear all; close all;
[angle5, torque5] = dataload("240105_8pi_H40K0.csv",[-3.5,0],[0.9290 0.6940 0.1250]	);
[angle3, torque3] = dataload("240105_8pi_H40K15.csv",[1-3.5,0],[0.6350 0.0780 0.1840]);
[angle1, torque1] = dataload("240105_8pi_H0K0_1.csv",[-5,0],[0.4660 0.6740 0.1880]);
% [angle4, torque4] = dataload("240105_8pi_H5K10.csv",[-3.5,0],'y');
[angle2, torque2] = dataload("240105_8pi_H25K60.csv",[1.5-3.5,0],[0 0.4470 0.7410]);
angle_tot=[angle5;angle3;angle1;angle2];
torque_tot=[torque5;torque3;torque1;torque2];
close all;
%%
angle_tot_pos=angle_tot(find(angle_tot>0));
torque_tot_pos=torque_tot(find(angle_tot>0));
angle_tot_neg=angle_tot(find(angle_tot<0));
torque_tot_neg=torque_tot(find(angle_tot<0));
p_pos=polyfit(angle_tot_pos,torque_tot_pos,3);
kappa_pos=p_pos(1)*angle_tot_pos.^2+p_pos(2)*angle_tot_pos+p_pos(3);
error_tot_pos=abs(torque_tot_pos-kappa_pos.*angle_tot_pos)./abs(kappa_pos.*angle_tot_pos);
p_neg=polyfit(angle_tot_neg,torque_tot_neg,3);
kappa_neg=p_neg(1)*angle_tot_neg.^2+p_neg(2)*angle_tot_neg+p_neg(3);
error_tot_neg=abs(torque_tot_neg-kappa_neg.*angle_tot_neg)./abs(kappa_neg.*angle_tot_neg);
figure(4); hold on;
plot(angle_tot_pos, error_tot_pos);
plot(angle_tot_neg, error_tot_neg);
%%
Wf=0.12;
figure(1); hold on;
x1 = linspace(0,5,1000);
kappa_pos=p_pos(1)*x1.^2+p_pos(2)*x1+p_pos(3);
kappa_pos1=kappa_pos*(1+Wf);
kappa_pos2=kappa_pos*(1-Wf);
y1 = kappa_pos1.*x1; y2 = kappa_pos2.*x1;
plot(x1,y1,'k--',x1,y2,'k--');
inBetween = [y1,fliplr(y2)];
x2=[x1,fliplr(x1)];
fill(x2, inBetween, 'k','FaceAlpha',0.1,'EdgeColor','none');
x1 = linspace(-5,0,1000);
kappa_neg=p_neg(1)*x1.^2+p_neg(2)*x1+p_neg(3);
kappa_neg1=kappa_neg*(1+Wf);
kappa_neg2=kappa_neg*(1-Wf);
y1 = kappa_neg1.*x1; y2 = kappa_neg2.*x1;
plot(x1,y1,'k--',x1,y2,'k--');
inBetween = [y1,fliplr(y2)];
x2=[x1,fliplr(x1)];
fill(x2, inBetween, 'k','FaceAlpha',0.1,'EdgeColor','none');
[angle5, torque5] = dataload("240105_8pi_H40K0.csv",[-3.5,0],[0.9290 0.6940 0.1250]	);
[angle3, torque3] = dataload("240105_8pi_H40K15.csv",[1-3.5,0],[0.6350 0.0780 0.1840]);
[angle1, torque1] = dataload("240105_8pi_H0K0_1.csv",[-5,0],[0.4660 0.6740 0.1880]);
% [angle4, torque4] = dataload("240105_8pi_H5K10.csv",[-3.5,0],'y');
[angle2, torque2] = dataload("240105_8pi_H25K60.csv",[1.5-3.5,0],[0 0.4470 0.7410]);
angle_tot=[angle5;angle3;angle1;angle2];
torque_tot=[torque5;torque3;torque1;torque2];

figure(1); hold on;
x1=linspace(-1.6,0,1000);
y1=p_neg(1)*x1.^3+p_neg(2)*x1.^2+p_neg(3)*x1;
plot(x1,y1,'k', LineWidth=2);
x2=linspace(0,1.74,1000);
y2=p_pos(1)*x2.^3+p_pos(2)*x2.^2+p_pos(3)*x2;
plot(x2,y2,'k', LineWidth=2)

legend('','','Uncertainty model','','','','0%','10%', '40%', '70%',Location='southeast')
ylim([-2.1 2.6]); xlabel('Torsional deflection (rad)',FontName='Times New Roman'); ylabel('Torque (Nm)',FontName='Times New Roman');
xlim([-1.6 1.74]);
set(gca,'fontname','Times New Roman')  % Set it to times
%%
angle_tot_pos=angle_tot(find(angle_tot>0));
torque_tot_pos=torque_tot(find(angle_tot>0));
angle_tot_neg=angle_tot(find(angle_tot<0));
torque_tot_neg=torque_tot(find(angle_tot<0));
p_pos=polyfit(angle_tot_pos,torque_tot_pos,3);
kappa_pos=p_pos(1)*angle_tot_pos.^2+p_pos(2)*angle_tot_pos+p_pos(3);
error_tot_pos=abs(torque_tot_pos-kappa_pos.*angle_tot_pos)./abs(kappa_pos.*angle_tot_pos);
p_neg=polyfit(angle_tot_neg,torque_tot_neg,3);
kappa_neg=p_neg(1)*angle_tot_neg.^2+p_neg(2)*angle_tot_neg+p_neg(3);
error_tot_neg=abs(torque_tot_neg-kappa_neg.*angle_tot_neg)./abs(kappa_neg.*angle_tot_neg);
figure(4); hold on;
plot(angle_tot_pos, error_tot_pos);
plot(angle_tot_neg, error_tot_neg);
%%
Wf=0.15;
figure(3); hold on;
x1 = linspace(0,5,1000);
kappa_pos=p_pos(1)*x1.^2+p_pos(2)*x1+p_pos(3);
kappa_pos_l=0.232*x1.^2-0.062*x1-0.426;
kappa_pos1=kappa_pos*(1+Wf)-kappa_pos_l;
kappa_pos2=kappa_pos*(1-Wf)-kappa_pos_l;
y1 = kappa_pos1.*x1; y2 = kappa_pos2.*x1;
plot(x1,y1,'k--',x1,y2,'k--');
inBetween = [y1,fliplr(y2)];
x2=[x1,fliplr(x1)];
fill(x2, inBetween, 'k','FaceAlpha',0.1,'EdgeColor','none');
x1 = linspace(-5,0,1000);
kappa_neg=p_neg(1)*x1.^2+p_neg(2)*x1+p_neg(3);
kappa_neg_l=-0.246*x1.^2-0.773*x1-0.610;
kappa_neg1=kappa_neg*(1+Wf)-kappa_neg_l;
kappa_neg2=kappa_neg*(1-Wf)-kappa_neg_l;
y1 = kappa_neg1.*x1; y2 = kappa_neg2.*x1;
plot(x1,y1,'k--',x1,y2,'k--');
inBetween = [y1,fliplr(y2)];
x3=linspace(-5,5,1000);
plot(x3, x3*1.157, 'k',LineWidth=1.5);
x2=[x1,fliplr(x1)];
fill(x2, inBetween, 'k','FaceAlpha',0.1,'EdgeColor','none');
ylim([-2.1 2.6]); xlabel('Torsional deflection (rad)',FontName='Times New Roman'); ylabel('Torque (Nm)',FontName='Times New Roman');
xlim([-1.6 1.74]);
set(gca,'fontname','Times New Roman')  % Set it to times
linearized_stiffness(angle5, torque5,[0.9290 0.6940 0.1250]);
linearized_stiffness(angle3, torque3,[0.6350 0.0780 0.1840]);
linearized_stiffness(angle1, torque1,[0.4660 0.6740 0.1880]);
linearized_stiffness(angle2, torque2,[0 0.4470 0.7410]);


figure(3); hold on;

plot(x3, x3*1.157, 'k',LineWidth=1.5);
legend('','','Uncertainty model','','','Nonimal stiffness','','G.C 0%','','G.C 10%','','G.C 40%','','G.C 70%')
% [angle3, torque3] = dataload("240105_8pi_H40K15.csv",[1-3.5,0],[0.6350 0.0780 0.1840]);
% [angle1, torque1] = dataload("240105_8pi_H0K0_1.csv",[-5,0],[0.4660 0.6740 0.1880]);
% % [angle4, torque4] = dataload("240105_8pi_H5K10.csv",[-3.5,0],'y');
% [angle2, torque2] = dataload("240105_8pi_H25K60.csv",[1.5-3.5,0],[0 0.4470 0.7410]);
function [angle, torque] = dataload(dataname, bias, color)
    data=readmatrix(dataname);
    data=data(2:end,:);
    angle = data(:,1)-bias(1);
    angle = deg2rad(angle);
    torque = data(:,2)-bias(2);
    figure(1); hold on;
    plot(angle(997:2997,1), torque(997:2997,1), "LineWidth",1,"Color",color);
end
function linearized_stiffness(angle, torque, color)
    angle_pos=angle(find(angle>0));
    torque_pos=torque(find(angle>0));
    angle_neg=angle(find(angle<0));
    torque_neg=torque(find(angle<0));
    kappa_pos=0.232*angle_pos.^2-0.062*angle_pos-0.426;
    torque_pos_input=torque_pos-kappa_pos.*angle_pos;
    kappa_neg=-0.246*angle_neg.^2-0.773*angle_neg-0.610;
    torque_neg_input=torque_neg-kappa_neg.*angle_neg;
    figure(3); hold on;
    plot(angle_pos, torque_pos_input, "LineWidth",0.5,"Color",color);
    plot(angle_neg, torque_neg_input, "LineWidth",0.5,"Color",color);
end