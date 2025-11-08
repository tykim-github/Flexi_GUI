function [Gzpet] = zpetc(varargin)
% Zero Phase Error Tracking Control
% Program by K.C. Kong
% 
% [Gzpet]=zpetc(Gsystem)
% 
% Gsystem must be in discrete time domain
%
% R(z) = Gzpet(z)*Yd(z)

if length(varargin)>1,
    error('Too many inputs');
end
if isa(varargin{1},'tf')==0,
    error('Transfer function required');
end

clc;
Gclosed = varargin{1};

% Gclosed = tf([1 -2 3 -1],[1 3 54 2 1],0.001);

[num,den,Ts]=tfdata(Gclosed,'v');
if length(num)>length(den),
    error('Improper model');
end

[Z,P,K] = tf2zpk(num,den);

j = 0;
k = 0;

Zu = [];
Zs = [];

for i=1:length(Z),
    if abs(Z(i)) >= 0.999999,
        j = j+1;
        Zu(j) = Z(i);
    else
        k = k+1;
        Zs(k) = Z(i);
    end
end

disp(strcat(num2str(j), ' unstable zero(s) detected.'));

F1 = zpk(P, Zs, K^-1, Ts);
% [N1,D1] = tfdata(F1temp,'v');
% F1 = tf(N1,D1,Ts);

F2temp = zpk(Zu, [], 1, Ts);
Gain = dcgain(F2temp);

if Gain == inf,
    Gain = bode(F2temp, 2*pi);
    disp('DC-gain is infinity. The magnitude is matched at 1Hz.');
end

[N,D] = tfdata(F2temp,'v');

for p = 1:(j+1),
    Nu(j-p+2) = N(p);
end
Du = zeros(1,(j+1));
Du(1) = 1;

F2 = tf(Nu, Du, Ts);
% [Zf, Pf, Kf] = tf2zpk(Nu,Du);

F = F1*F2/Gain^2;
% Temp = zpk([P; Zf],[Zs'; Pf],K^-1*Kf,Ts) / Gain^2;
%Gzpet = minreal(F);
Gzpet = F;

figure;
bode(Gclosed,'k:'); grid on;
hold;
bode(Gzpet,'k--');
bode(minreal(Gzpet*Gclosed),'k');
legend('G_S_Y_S_T_E_M','G_Z_P_E_T_C','G_O_V_E_R_A_L_L');

[Az,Bz] = tfdata(F,'v');
nz = length(roots(Az));
np = length(roots(Bz));
d = nz - np;

ControlLaw = 'r(k)=';

for i=(d+2):nz+1,
    if Bz(i)~=0,
        ControlLaw = strcat( ControlLaw,'+', num2str(-Bz(i),14), '*r(k', num2str(d-i+1),')' );
    end
end
for i=1:d,
    if Az(i)~=0,
        ControlLaw = strcat( ControlLaw, '+', num2str(Az(i),14), '*Yd(k+', num2str(d-(i-1)),')' );
    end
end
    if Az(d+1)~=0,
        ControlLaw = strcat( ControlLaw, '+', num2str(Az(d+1),14), '*Yd(k)');
    end
for i=d+2:nz+1,
    if Az(i)~=0,
        ControlLaw = strcat( ControlLaw, '+', num2str(Az(i),14), '*Yd(k', num2str(d-(i-1)),')' );
    end
end

ControlLaw_labview = 'r=';
for i=(d+2):nz+1,
    if Bz(i)<0,
        ControlLaw_labview = strcat( ControlLaw_labview,'+', num2str(-Bz(i),14), '*r', num2str(i-d-1) );
    elseif Bz(i)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(-Bz(i),14), '*r', num2str(i-d-1) );
    end
end
for i=1:d,
    if Az(i)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, '+', num2str(Az(i),14), '*ydf', num2str(d-(i-1)) );
    elseif Az(i)<0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(Az(i),14), '*ydf', num2str(d-(i-1)) );
    end
end
    if Az(d+1)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, '+', num2str(Az(d+1),14), '*yd');
    elseif Az(d+1)<0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(Az(d+1),14), '*yd');
    end
for i=d+2:nz+1,
    if Az(i)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, '+', num2str(Az(i),14), '*yd', num2str(i-d-1));
    elseif Az(i)<0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(Az(i),14), '*yd', num2str(i-d-1) );
    end
end
ControlLaw_labview = strcat(ControlLaw_labview, ';')


disp('----------------------------Control Law----------------------------');
disp('-------------------------------------------------------------------');
disp(ControlLaw);
disp('--------------Control law for LabVIEW formula mode ----------------');
disp(ControlLaw_labview)