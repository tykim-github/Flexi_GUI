function [sys, Uncertainty, R, O, X] = freqid(varargin)
% Frequency response identification
% Programed by K.C.Kong
%
% Example (1)
% sys = freqid(wdata,mdata);
% where,
%    wdata = excitation frequencies (rad/sec)
%    mdata = frequency responses of plant (lin)
% ------------------------------------------------------------------------
% Example (2)
% sys = freqid(wdata,mdata,pdata);
% where,
%    pdata = phase delay (degree(180))
% ------------------------------------------------------------------------
% Example (3)
% sys = freqid(wdata,mdata,[n m]);
% where,
% n = # of poles
% m = # of zeros
% ------------------------------------------------------------------------
% Example (4)
% sys = freqid(wdata,mdata,[n m i]);
% where,
%    n = # of poles (including # of integrator)
%    m = # of zeros
%    i = # of integrator (<=3)

wdata = varargin{1};
mdata = varargin{2};
isPdata = 0; %If pdata is inserted, then 1
isOrdervec = 0; %If order vector is inserted, then 1
isInitialSys = 0; %If initial Sys is inserted, then 1

clc;

if (length(wdata) ~= length(mdata)),
    error('Lengths of wdata and mdata mismatch');
end

for i=3:length(varargin),
    if length(varargin{i})==length(wdata),
        pdata=varargin{i};
        disp('Phase data loaded');
        isPdata = 1;
        
    elseif length(varargin{i})==2,
        n=varargin{i}(1);       %# of poles
        m=varargin{i}(2);      %# of zeros
        n_int=0;
        isOrdervec = 1; 
        disp('Order vector loaded');
        
        if n==0,
            error('Number of poles must be greater than zero');
        end
        if n<m,
            disp('Improper model');
        end       
        
    elseif length(varargin{i})==3,
        n=varargin{i}(1);       %# of poles
        m=varargin{i}(2);      %# of zeros
        n_int=varargin{i}(3); %# of integrators
        isOrdervec = 1; 
        disp('Order vector loaded');
        
        if n==0,
            error('Number of poles must be greater than zero');
        end
        if n<m,
            disp('Improper model');
        end        
        if (n-n_int)<0,
            error('Number of integrators exceeds the number of poles');
        end
        if n_int>3,
            error('Number of integrators must be less than four')
        end
        
    elseif length(varargin{i})==1,
        if isa(varargin{i},'tf')==1,
            isInitialSys = 1;
            disp('Initial model loaded');
            Gint=minreal(varargin{i});
        end
    end
end

if isInitialSys == 1 && isOrdervec == 0,
    n=length(pole(Gint));
    m=length(zero(Gint));
    n_int=0;
    isOrdervec = 1;
    disp('Since you entered the initial model, the order is fixed as the initial model');
end

if length(wdata*wdata')==1,
    W=wdata';
else
    W=wdata;
end

if length(mdata*mdata')==1,
    Y=mdata';
else
    Y=mdata;
end

disp('');

if isOrdervec==0,
    n=input('Number of poles (including integrators)?');
        if n==0,
            error('Number of poles must be greater than zero');
        end
    m=input('Number of zeros?');
    n_int=input('Number of integrators? <= 3');
        if (n-n_int)<0,
            error('Number of integrators exceeds the number of poles');
        elseif (n_int>3),
            error('Too many integrators')
        end
end

Gmag='abs( (';
for i=m:-1:0,
    term=strcat('+b',num2str(i),'*(x*j)^',num2str(i));
    Gmag=strcat(Gmag,term);
end
    Gmag=strcat(Gmag,')/((x*j)^',num2str(n));
if n~=n_int,
    for i=(n-1):-1:n_int,
    term=strcat('+a',num2str(i),'*(x*j)^',num2str(i));
    Gmag=strcat(Gmag,term);
    end
end
    Gmag=strcat(Gmag,') )');

    if isInitialSys == 0,
        Initial = abs(randn([1,(n+m+1-n_int)]).*[1000 1]);
        disp('Initial values are set to random numbers');
    elseif isInitialSys == 1,
        [Nint, Dint]=tfdata(Gint,'v');
        Nn=length(Nint);
        Initial = zeros([1,(n+m+1-n_int)]);
        Initial = [Dint( (Nn-n_int):-1:(Nn-n+1) ) Nint( Nn:-1:(Nn-m) )];
    end
    
type=fittype(Gmag);
F=fitoptions('method','NonlinearLeastSquares','Display','iter','MaxIter',2000,'MaxFunEvals',1000,'StartPoint',Initial);
[X,R,O]=fit(W,Y,type,F);

if n_int==0,
    if n==1,
        a0 = X.a0;
    elseif n==2,
        a0 = X.a0;
        a1 = X.a1;
    elseif n>2,
        a0 = X.a0;
        a1 = X.a1;
        a2 = X.a2;
    end
end

if n_int==1,
    if n==1,
        a0 = 0;
    elseif n==2,
        a0 = 0;
        a1 = X.a1;
    elseif n>2,
        a0 = 0;
        a1 = X.a1;
        a2 = X.a2;
    end
end

if n_int==2,
    if n==1,
        a0 = 0;
    elseif n==2,
        a0 = 0;
        a1 = 0;
    elseif n>2,
        a0 = 0;
        a1 = 0;
        a2 = X.a2;
    end
end

if n_int==3,
    if n==1,
        a0 = 0;
    elseif n==2,
        a0 = 0;
        a1 = 0;
    elseif n>2,
        a0 = 0;
        a1 = 0;
        a2 = 0;
    end
end

if n==1,
    num=[1 a0];
elseif n==2,
    num=[1 a1 a0];
elseif n==3,
    num=[1 a2 a1 a0];
elseif n==4,
    num=[1 X.a3 a2 a1 a0];
elseif n==5,
    num=[1 X.a4 X.a3 a2 a1 a0];
elseif n==6,
    num=[1 X.a5 X.a4 X.a3 a2 a1 a0];
elseif n==7,
    num=[1 X.a6 X.a5 X.a4 X.a3 a2 a1 a0];
elseif n==8,
    num=[1 X.a7 X.a6 X.a5 X.a4 X.a3 a2 a1 a0];
elseif n==9,
    num=[1 X.a8 X.a7 X.a6 X.a5 X.a4 X.a3 a2 a1 a0];
elseif n==10,
    num=[1 X.a9 X.a8 X.a7 X.a6 X.a5 X.a4 X.a3 a2 a1 a0];
end

if m==0,
    den=[X.b0];
elseif m==1,
    den=[X.b1 X.b0];
elseif m==2,
    den=[X.b2 X.b1 X.b0];
elseif m==3,
    den=[X.b3 X.b2 X.b1 X.b0];
elseif m==4,
    den=[X.b4 X.b3 X.b2 X.b1 X.b0];
elseif m==5,
    den=[X.b5 X.b4 X.b3 X.b2 X.b1 X.b0];
elseif m==6,
    den=[X.b6 X.b5 X.b4 X.b3 X.b2 X.b1 X.b0];
elseif m==7,
    den=[X.b7 X.b6 X.b5 X.b4 X.b3 X.b2 X.b1 X.b0];
elseif m==8,
    den=[X.b8 X.b7 X.b6 X.b5 X.b4 X.b3 X.b2 X.b1 X.b0];
elseif m==9,
    den=[X.b9 X.b8 X.b7 X.b6 X.b5 X.b4 X.b3 X.b2 X.b1 X.b0];
elseif m==10,
    den=[X.b10 X.b9 X.b8 X.b7 X.b6 X.b5 X.b4 X.b3 X.b2 X.b1 X.b0];
end

W=[0:9999]/9999*(wdata(length(wdata))-wdata(1))+wdata(1);

SysTemp=tf(den,num);
P=pole(SysTemp);
Z=zero(SysTemp);
    for i=1:length(P);
        if real(P(i))>0,
            P(i)=-P(i);
        end
    end
    for i=1:length(Z);
        if real(Z(i))>0,
            Z(i)=-Z(i);
        end
    end

sysZPK=zpk(Z,P,abs(den(1)));
sys=tf(sysZPK);

[m,p]=bode(sys,W);

for i=1:length(W),
    magsys(i)=m(i);
    psys(i)=p(i);
end

if isInitialSys == 1,
    [mint,pint]=bode(Gint,W);
    for i=1:length(W),
        magsysInt(i)=mint(i);
        psysInt(i)=pint(i);
    end
end

if isPdata==0,
    figure; 
    semilogx(wdata,20*log10(mdata),'ko');
    hold on;
    semilogx(W,20*log10(magsys),'k');
    xlabel('Frequency(rad/sec)');
    ylabel('dB');
    legend('data','curve fit');
    grid on;
    
    if isInitialSys == 1,
        semilogx(W,20*log10(magsysInt),'r');
        legend('data','curve fit','Initial model');
    end
    
elseif isPdata==1,
    figure; 
    subplot(211),semilogx(wdata,20*log10(mdata),'ko');
    hold on;
    semilogx(W,20*log10(magsys),'k');
    xlabel('Frequency(rad/sec)');
    ylabel('dB');
    legend('data','curve fit');
    grid on;
    
    if isInitialSys == 1,
        semilogx(W,20*log10(magsysInt),'r');
        legend('data','curve fit','Initial model');
    end

    subplot(212),semilogx(wdata,pdata,'ko');
    hold on;
    semilogx(W,psys,'k');
    grid on;
    
    if isInitialSys == 1,
        semilogx(W,psysInt,'r');
        legend('data','curve fit','Initial model');
    end
    
    [mn,pn]=bode(sys,wdata);

    for i=1:length(wdata),
        Uncertainty(i) = mdata(i)/mn(i)*exp(j*pi/180*(pdata(i)-pn(i))) - 1;
        maguncertainty(i)=real(Uncertainty(i));
        psyuncertainty(i)=angle(Uncertainty(i));
    end
    figure;
        semilogx(wdata,20*log10(maguncertainty),'k');
        title('Model uncertainty');
        xlabel('Frequency(rad/sec)');
        ylabel('dB');
        grid on;
end
