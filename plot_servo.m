function plot_servo(filename)
data=csvread(strcat('/home/haptics/joshdata/', filename));
pos = data(:, 1);
time = data(:, 2);
mag = sqrt(data(:,3).*data(:,3) + data(:,4).*data(:,4) + data(:,5).*data(:,5));

x = median(mag)
y = mean(mag)
disp x
disp y

save(strcat(filename, '.mat'),'data')

figure(1);
%plot 1:  position vs time
subplot(2,1,1);
plot(time, pos);
title('Position vs. Time');
axis([0 max(time) 0 max(pos)]);

%plot 2: magnitude vs time
subplot(2,1,2);
plot(time, mag);
title('Magnitude vs. Time');
axis([0 max(time) 0 max(mag)]);
