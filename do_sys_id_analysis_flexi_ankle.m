
function results = do_sys_id_analysis_flexi_ankle(t_filename)

% (1) Enter proper file name
filename = sprintf('%s.txt', t_filename);
data=importdata(filename, '\t', 1);  % 첫 번째 줄은 헤더로 읽어들임

% (3) 열 데이터를 변수로 분리
% cnt freq cur force enc1 motor_vel
raw_data=data.data;
unique_rows = [true; diff(raw_data(:,1)) ~= 0];
filtered_data = raw_data(unique_rows, :);
cnt=filtered_data(:,1);
% figure(101); plot(cnt);
freq=filtered_data(:,2);
cur=filtered_data(:,3);
force=filtered_data(:,4);
vel_ref=filtered_data(:,5);
mot_vel=filtered_data(:,6);
cnt_vel=cnt-circshift(cnt, 1);
idx = find(cnt_vel<0,1,"last");

% cnt=cnt(idx:2:end);
% freq=freq(idx:2:end);
% cur=cur(idx:2:end);
% force=force(idx:2:end);
% enc=enc(idx:2:end);
% mot_vel=mot_vel(idx:2:end);
cnt=cnt(idx:end);
freq=freq(idx:end);
cur=cur(idx:end);
force=force(idx:end);
vel_ref=vel_ref(idx:end);
mot_vel=mot_vel(idx:end);
% figure(100);
% plot(cur); hold on; plot(vel_ref);
% figure(101);
% hold on; plot(cnt);
%% Spline Data
len=length(cnt);
new_cnt = 1:len;
%splined_cnt  = spline(cnt,cnt,new_cnt);
splined_freq = freq;
%splined_freq = spline(cnt,freq,new_cnt);
disp(length(cnt));
disp(length(new_cnt))
% splined_cur  = spline(cnt,cur,new_cnt);
% splined_spring_ang  = spline(cnt,spring_ang,new_cnt);
splined_cur  = vel_ref;
splined_spring_ang  = force;

%% Divide frequency by frequency

t_freq = 0; %dummy value
j = 0;
N = 1;

for i = 1:len
    
    if (floor(splined_freq(i)*1000)/1000 ~= floor(t_freq*1000)/1000)
        t_freq = splined_freq(i);
        j = j+1;
        frequency_samples(j) = t_freq; 
        N = 1;
    end

    if(j > 0)
        cell_cur{j}(N) = splined_cur(i);
        cell_vel{j}(N) = splined_spring_ang(i);
        N = N+1;
    end

end
disp("first_freq:"+num2str(frequency_samples(2)));
disp("last_freq:"+num2str(frequency_samples(3)));
N_samples = length(frequency_samples)


%% Bandpass filtering

band_range = 0.3;
n = 2;

for i = 1:N_samples

    d = designfilt('bandpassiir','FilterOrder', n, ...
               'HalfPowerFrequency1',(frequency_samples(i)-frequency_samples(i)*band_range),'HalfPowerFrequency2',(frequency_samples(i)+frequency_samples(i)*band_range), ...
                'DesignMethod', "butter", 'SampleRate',1000);

    cell_filter_cur{i} = filtfilt(d, cell_cur{i});
    cell_filter_vel{i} = filtfilt(d, cell_vel{i});
    
end



%% Remove the Transient Section


for i = 1:N_samples
    
%     cell_cutted_cur{i} = cell_filter_cur{i}(fix(end/2):end);
%     cell_cutted_vel{i} = cell_filter_vel{i}(fix(end/2):end);
    cell_cutted_cur{i} = cell_filter_cur{i}(fix(end*0.25):fix(end*0.75));
    cell_cutted_vel{i} = cell_filter_vel{i}(fix(end*0.25):fix(end*0.75));
    % figure(i); plot(cell_vel{i},'k'); hold on; plot(cell_filter_vel{i},'b'); plot(cell_filter_cur{i}*10,'r'); 
    
end


%% Current FFT 

fs = 1000;

% for i = 1:N_samples
for i = 1:N_samples

    L = length(cell_cutted_cur{i});
    y_input = fft(cell_cutted_cur{i});
    P2_input = y_input/L;
    P1_input = P2_input(1:fix(L/2)+1);
    P1_input(2:end-1) = 2*P1_input(2:end-1);

    y_output = fft(cell_cutted_vel{i});
    P2_output = y_output/L;
    P1_output = P2_output(1:fix(L/2)+1);
    P1_output(2:end-1) = 2*P1_output(2:end-1);
    
    index = fix(frequency_samples(i)*L/1000 + 1);

    tf_val = P1_output(index)/P1_input(index);
    
    tf_mag(i) = 20*log10(abs(tf_val));
    tf_phase(i) = 180/pi*angle(tf_val);
    if(tf_phase(i)>20) tf_phase(i)=tf_phase(i)-360; end
end
%%
datamatrix = [frequency_samples', tf_mag', tf_phase']; 

name = sprintf('Frequency_domain_%s.txt', t_filename);
writematrix(datamatrix, name);