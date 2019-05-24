%%% For Example 28; To use Gurobi solver you have to obtain the free academic license of gurobi
%%% If you prefer to use the default solvers of cvx, just quote the line
%%% cvx_solver gurobi
close all
clear all
clc


A=[1.1 2; 0 0.95];
B=[0 1;0.0787 0];
C=[-1 1];
D=0;

Q=C'*C;
R=0.01*C'*C;


N=2; % Can change N to see the performance of different N
M_cell=cell(N,1);
for i=1:N
    M_cell(i,1)={A^i};
end
M=cell2mat(M_cell);

C_dec_cell=cell(N);
for i=1:N
    for j=1:N
        if i>=j
            C_dec_cell(i,j)={B};
        else
            C_dec_cell(i,j)={zeros(size(B))};
        end
    end
end

for i=1:N
    for j=1:N
        if i>j
            C_dec_cell(i,j)={A^(i-j)*C_dec_cell{i,j}};
        end
    end
end
C_dec=cell2mat(C_dec_cell);


[K_infty,P_infty]=dlqr(A,B,Q,R);
K_infty=-K_infty;


K_infty

Q_bar=dlyap((A+B*K_infty)',Q+K_infty'*R*K_infty)

R_tilde_cell=cell(N);
Q_tilde_cell=cell(N);
for i=1:N
    for j=1:N
        if i==j
            if i==N
                R_tilde_cell(i,j)={R};
                Q_tilde_cell(i,j)={Q_bar};
            else
            R_tilde_cell(i,j)={R};
            Q_tilde_cell(i,j)={Q};
            end
        else
            R_tilde_cell(i,j)={zeros(size(R))};
            Q_tilde_cell(i,j)={zeros(size(Q))};
        end
    end
end

R_tilde=cell2mat(R_tilde_cell);
Q_tilde=cell2mat(Q_tilde_cell);

H=C_dec'*Q_tilde*C_dec+R_tilde
F=C_dec'*Q_tilde*M
G=M'*Q_tilde*M+Q

A_c_cell=cell(2,1);
A_c_cell(1,1)={eye(N)};
A_c_cell(2,1)={-eye(N)};
A_c=cell2mat(A_c_cell);

b_0=ones(2*N,1);

B_x=zeros(2*N,length(A));



% Q_bar=dlyap(A+B*K_infty,Q)
% K_infty=K_pred(1,:);



K_time=100;
% x_ol=zeros(3,K_time);
x_cl=zeros(2,K_time);
x_cl(:,1)=[0.5;-0.5]; % Can change initial state to observe different performance
% x_cl(:,1)=[0.8;-0.8];

% y_ol=zeros(K_time,1);
y_cl=zeros(K_time,1);

% u_ol=zeros(K_time,1);
u_cl=zeros(K_time,1);

x_pred=x_cl;
y_pred=zeros(K_time,1);
J_record=zeros(K_time,1);

for k=1:K_time-1
    k
    cvx_begin quiet
    cvx_solver gurobi
    variable u(N)
    minimize (u'*H*u+2*x_cl(:,k)'*F'*u)
    subject to 
    u>=-1
    u<=1
    cvx_end
    u_cl(k)=u(1);
    y_cl(k)=C*x_cl(:,k);
    x_cl(:,k+1)=A*x_cl(:,k)+B*u_cl(k);
    J_record(k,1)=u'*H*u+2*x_cl(:,k)'*F'*u+x_cl(:,k)'*G*x_cl(:,k);
end



t=0:1:0+K_time-1;

figure(1)
subplot(2,1,1)
% stairs(t,y_ol)
stairs(t,u_cl,'b-o')
xlim([0 K_time-N])
% hold on
% stairs(0:N-1,u_seq,'r-+')
% stairs(t,r*ones(K_time,1))

subplot(2,1,2)
% stairs(t,u_ol)
plot(t,y_cl,'b-o')
% hold on
% plot(0:N,y_pred(1:N+1),'r-+')
xlim([0 K_time-N])

figure(2)
plot(J_record)
xlim([0 K_time-N])

