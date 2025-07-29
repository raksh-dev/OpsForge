import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Progress, List, Tag, Space, Spin } from 'antd';
import { Link } from 'react-router-dom';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  WarningOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { Line, Pie } from '@ant-design/charts';
import { useQuery } from 'react-query';
import { employeeAPI, taskAPI, agentAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import moment from 'moment';
import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const [attendanceStatus, setAttendanceStatus] = useState(null);

  // Fetch attendance status
  const { data: attendance } = useQuery(
    ['attendance', user?.id],
    () => employeeAPI.getAttendance(user.id, {
      start_date: moment().format('YYYY-MM-DD'),
      end_date: moment().format('YYYY-MM-DD'),
    }),
    { enabled: !!user }
  );

  // Fetch tasks
  const { data: tasks } = useQuery(
    ['tasks', user?.id],
    () => taskAPI.list({ assignee_id: user.id }),
    { enabled: !!user }
  );

  // Fetch recent agent actions
  const { data: agentActions } = useQuery(
    'recentAgentActions',
    () => agentAPI.getHistory({ limit: 5 })
  );

  useEffect(() => {
    if (attendance?.data?.length > 0) {
      const todayRecord = attendance.data[0];
      if (todayRecord.clock_out) {
        setAttendanceStatus('clocked_out');
      } else {
        setAttendanceStatus('clocked_in');
      }
    } else {
      setAttendanceStatus('not_clocked_in');
    }
  }, [attendance]);

  // Calculate task statistics
  const taskStats = {
    total: tasks?.data?.length || 0,
    completed: tasks?.data?.filter(t => t.status === 'completed').length || 0,
    inProgress: tasks?.data?.filter(t => t.status === 'in_progress').length || 0,
    todo: tasks?.data?.filter(t => t.status === 'todo').length || 0,
    overdue: tasks?.data?.filter(t => 
      t.due_date && moment(t.due_date).isBefore(moment()) && t.status !== 'completed'
    ).length || 0,
  };

  // Weekly hours data (mock for now)
  const weeklyHoursData = [
    { day: 'Mon', hours: 8.5 },
    { day: 'Tue', hours: 7.8 },
    { day: 'Wed', hours: 8.2 },
    { day: 'Thu', hours: 9.1 },
    { day: 'Fri', hours: 7.5 },
  ];

  const weeklyHoursConfig = {
    data: weeklyHoursData,
    xField: 'day',
    yField: 'hours',
    smooth: true,
    point: { size: 4, shape: 'circle' },
    label: { style: { fill: '#aaa' } },
  };

  // Task distribution data
  const taskDistributionData = [
    { type: 'To Do', value: taskStats.todo },
    { type: 'In Progress', value: taskStats.inProgress },
    { type: 'Completed', value: taskStats.completed },
  ];

  const taskDistributionConfig = {
    data: taskDistributionData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: { 
      type: 'outer'
    },
    interactions: [{ type: 'pie-legend-active' }, { type: 'element-active' }],
  };

  return (
    <div className="dashboard">
      {/* Welcome Section */}
      <Card className="welcome-card">
        <h2>Welcome back, {user?.full_name}!</h2>
        <p>Here's your overview for {moment().format('dddd, MMMM D, YYYY')}</p>
      </Card>

      {/* Quick Stats */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Attendance Status"
              value={attendanceStatus === 'clocked_in' ? 'Clocked In' : 'Clocked Out'}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ 
                color: attendanceStatus === 'clocked_in' ? '#52c41a' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Tasks"
              value={taskStats.inProgress}
              prefix={<SyncOutlined spin />}
              suffix={`/ ${taskStats.total}`}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Completed This Week"
              value={taskStats.completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Overdue Tasks"
              value={taskStats.overdue}
              prefix={<WarningOutlined />}
              valueStyle={{ color: taskStats.overdue > 0 ? '#ff4d4f' : '#000' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Weekly Hours">
            <Line {...weeklyHoursConfig} height={250} />
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Task Distribution">
            <Pie {...taskDistributionConfig} height={250} />
          </Card>
        </Col>
      </Row>

      {/* Lists Section */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card 
            title="Upcoming Tasks" 
            extra={<Link to="/tasks">View All</Link>}
          >
            <List
              dataSource={tasks?.data?.filter(t => t.status !== 'completed').slice(0, 5)}
              renderItem={task => (
                <List.Item>
                  <List.Item.Meta
                    title={task.title}
                    description={
                      <Space>
                        <Tag color={
                          task.priority === 'urgent' ? 'red' :
                          task.priority === 'high' ? 'orange' :
                          task.priority === 'medium' ? 'blue' : 'default'
                        }>
                          {task.priority}
                        </Tag>
                        {task.due_date && (
                          <span>Due: {moment(task.due_date).format('MMM D')}</span>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
              empty={<div>No tasks assigned</div>}
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card 
            title="Recent AI Actions" 
            extra={<Link to="/agent-history">View All</Link>}
          >
            <List
              dataSource={agentActions?.actions}
              renderItem={action => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<RobotOutlined style={{ fontSize: 24 }} />}
                    title={action.agent_name}
                    description={
                      <Space direction="vertical" size={0}>
                        <span>{action.action_type}</span>
                        <span style={{ fontSize: 12, color: '#999' }}>
                          {moment(action.timestamp).fromNow()}
                        </span>
                      </Space>
                    }
                  />
                  <Tag color={action.success ? 'success' : 'error'}>
                    {action.success ? 'Success' : 'Failed'}
                  </Tag>
                </List.Item>
              )}
              empty={<div>No recent actions</div>}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;