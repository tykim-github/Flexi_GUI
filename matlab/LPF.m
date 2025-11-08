function [G] = LPF(varargin)

cutoff_freq=varargin{1};
order = varargin{2};

Ginv = minreal(1/G);                    %Gn^-1
[num,den,Ts]=tfdata(Ginv,'v');
Gden=tf(den,den,Ts);                %Gden = 1;

if length(varargin)<3,
    Qorder = [2 (2-n+m)];
else
    Qorder = varargin{3};
end

tau=varargin{2}*2*pi;
tauz=exp(-tau*Ts);
ZeroQ=ones(Qorder(2),1)*tauz;
PoleQ=ones(Qorder(1),1)*tauz;

Q=zpk(ZeroQ, PoleQ, 1, Ts);
Q=Q/dcgain(Q);

% d = Q(Ginv*Y-Ud)
Gy = Q*Ginv;
Gu = -Q*Gden;

[By,A]=tfdata(Gy,'v');
[Bu,A]=tfdata(Gu,'v');

ControlLaw = 'd(k)=';

n=length(A);
for i=2:n,
    ControlLaw = strcat( ControlLaw,'+', num2str(-A(i),14), '*d(k', num2str(-(i-1)),')' );
end
    if By(1)~=0,
        ControlLaw = strcat( ControlLaw, '+', num2str(By(1),14), '*Y(k)' );
    end
for i=2:n,
    if By(i)~=0,
        ControlLaw = strcat( ControlLaw, '+', num2str(By(i),14), '*Y(k', num2str(-(i-1)),')' );
    end
end
for i=1:n,
     if Bu(i)~=0,
         ControlLaw = strcat( ControlLaw, '+', num2str(Bu(i),14), '*ud(k', num2str(-(i-1)),')' );
     end
end

ControlLaw_labview = 'd=';
for i=2:n,
    if A(i)<0,
        ControlLaw_labview = strcat( ControlLaw_labview,'+', num2str(-A(i),14), '*d', num2str(i-1) );
    elseif A(i)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(-A(i),14), '*d', num2str(i-1) );
    end
end
    if By(1)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, '+', num2str(By(1),14), '*y' );
    elseif By(1)<0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(By(1),14), '*y' );
    end
for i=2:n,
    if By(i)>0,
        ControlLaw_labview = strcat( ControlLaw_labview, '+', num2str(By(i),14), '*y', num2str(i-1) );
    elseif By(i)<0,
        ControlLaw_labview = strcat( ControlLaw_labview, num2str(By(i),14), '*y', num2str(i-1) );
    end
end
for i=1:n,
     if Bu(i)>0,
         ControlLaw_labview = strcat( ControlLaw_labview, '+', num2str(Bu(i),14), '*ud', num2str(i-1) );
     elseif Bu(i)<0,
         ControlLaw_labview = strcat( ControlLaw_labview, num2str(Bu(i),14), '*ud', num2str(i-1) );
     end
end
ControlLaw_labview = strcat(ControlLaw_labview, ';')

ControlLaw_stm = 'posDOB.q_out[0] =';
for i=2:n,
    if A(i)<0,
        ControlLaw_stm = strcat( ControlLaw_stm,'+', num2str(-A(i),14), '*posDOB.q_out[', num2str(i-1),']' );
    elseif A(i)>0,
        ControlLaw_stm = strcat( ControlLaw_stm, num2str(-A(i),14), '*posDOB.q_out[', num2str(i-1),']' );
    end
end
    if By(1)>0,
        ControlLaw_stm = strcat( ControlLaw_stm, '+', num2str(By(1),14), '*posDOB.gq_in[0]' );
    elseif By(1)<0,
        ControlLaw_stm = strcat( ControlLaw_stm, num2str(By(1),14), '*posDOB.gq_in[0]' );
    end
for i=2:n,
    if By(i)>0,
        ControlLaw_stm = strcat( ControlLaw_stm, '+', num2str(By(i),14), '*posDOB.gq_in[', num2str(i-1),']' );
    elseif By(i)<0,
        ControlLaw_stm = strcat( ControlLaw_stm, num2str(By(i),14), '*posDOB.gq_in[', num2str(i-1),']' );
    end
end
for i=1:n,
     if Bu(i)>0,
         ControlLaw_stm = strcat( ControlLaw_stm, '+', num2str(Bu(i),14), '*posDOB.q_in[', num2str(i-1),']' );
     elseif Bu(i)<0,
         ControlLaw_stm = strcat( ControlLaw_stm, num2str(Bu(i),14), '*posDOB.q_in[', num2str(i-1),']' );
     end
end
ControlLaw_stm = strcat(ControlLaw_stm, ';')

clc;
disp('d=Gy*Y + Gu*Ud');
disp('where, Ud = U - d');

Gy
Gu
disp('----------------------------------------------------------------');
disp(ControlLaw);
disp('-----------------Control law for LabVIEW formula mode---------------------')
disp(ControlLaw_labview);
disp('-----------------Control law for STM code---------------------')
disp(ControlLaw_stm);