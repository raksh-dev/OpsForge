import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Space, Badge } from 'antd';
import {
  DashboardOutlined,
  ClockCircleOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
  RobotOutlined,
  HistoryOutlined,
  TeamOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import './Layout.css';

const { Header, Sider, Content } = Layout;

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isManager } = useAuth();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/attendance',
      icon: <ClockCircleOutlined />,
      label: 'Attendance',
    },
    {
      key: '/tasks',
      icon: <CheckSquareOutlined />,
      label: 'Tasks',
    },
    {
      key: '/reports',
      icon: <FileTextOutlined />,
      label: 'Reports',
    },
    {
      key: '/agent-chat',
      icon: <RobotOutlined />,
      label: 'AI Assistant',
    },
    {
      key: '/agent-history',
      icon: <HistoryOutlined />,
      label: 'Agent History',
    },
  ];

  // Add employees menu for managers
  if (isManager) {
    menuItems.push({
      key: '/employees',
      icon: <TeamOutlined />,
      label: 'Employees',
    });
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => navigate('/dashboard'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: () => {
        logout();
        navigate('/login');
      },
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        breakpoint="lg"
      >
        <div className="logo">
          <h2>{collapsed ? 'AI' : 'AI Operations'}</h2>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems.map(item => ({
            ...item,
            onClick: () => navigate(item.key),
          }))}
        />
      </Sider>
      
      <Layout>
        <Header className="site-header">
          <div className="header-content">
            <h1 className="page-title">
              {menuItems.find(item => item.key === location.pathname)?.label || 'AI Operations Agent'}
            </h1>
            
            <Space size="large">
              <Badge count={5}>
                <BellOutlined style={{ fontSize: '20px', cursor: 'pointer' }} />
              </Badge>
              
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
              >
                <Space style={{ cursor: 'pointer' }}>
                  <Avatar style={{ backgroundColor: '#1890ff' }}>
                    {user?.full_name?.charAt(0).toUpperCase()}
                  </Avatar>
                  <span>{user?.full_name}</span>
                </Space>
              </Dropdown>
            </Space>
          </div>
        </Header>
        
        <Content className="site-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;