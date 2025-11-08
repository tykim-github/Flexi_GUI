function [Gptc] = ptc(varargin)
% Perfect Tracking Control
% Program by K.C. Kong
% 
% [Gptc]=ptc(Gsystem)
% 
% Gsystem must be in discrete time domain
%
% R(z) = Gptc(z)*Yd(z)

if length(varargin)>1,
    error('Too many inputs');
end
if isa(varargin{1},'tf')==0,
    error('Transfer function required');
end

clc;
Gclosed = varargin{1};

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
if(j>0)
    error('G has unstable zeros');
end
z=tf('z');
Gptc=Gclosed^-1*z^(length(num)-length(den))



[Az,Bz] = tfdata(minreal(Gclosed^-1),'v');
nz = length(roots(Az));
np = length(roots(Bz));
d = nz - np;
Az=Az/Bz(d+1);
Bz=Bz/Bz(d+1);
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
ControlLaw_labview = strcat(ControlLaw_labview, ';');


disp('----------------------------Control Law----------------------------');
disp('-------------------------------------------------------------------');
disp(ControlLaw);
disp('--------------Control law for LabVIEW formula mode ----------------');
disp(ControlLaw_labview)