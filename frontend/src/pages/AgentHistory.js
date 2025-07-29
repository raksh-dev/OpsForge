import React, { useState } from 'react';
import { Table, Card, Tag, DatePicker, Select, Space, Button } from 'antd';
import { RobotOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery } from 'react-query';
import { agentAPI } from '../services/api';
import moment from 'moment';

const { RangePicker } = DatePicker;
const { Option } = Select;

const AgentHistory = () => {
  const [dateRange, setDateRange] = useState([moment().startOf('month'), moment().endOf('month')]);
  const [agentFilter, setAgentFilter] = useState('all');

  const { data: agentHistory, isLoading } = useQuery(
    ['agentHistory', dateRange, agentFilter],
    () => agentAPI.getAgentHistory({
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      agent_type: agentFilter !== 'all' ? agentFilter : undefined
    })
  );

  const columns = [
    {
      title: 'Agent',
      dataIndex: 'agent_type',
      key: 'agent_type',
      render: (type) => {
        const colors = {
          task_agent: 'blue',
          clock_agent: 'green',
          report_agent: 'orange'
        };
        return <Tag color={colors[type]} icon={<RobotOutlined />}>{type.replace('_', ' ').toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === 'completed' ? 'green' : status === 'failed' ? 'red' : 'blue';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'User',
      dataIndex: 'user_name',
      key: 'user_name',
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration) => duration ? `${duration}ms` : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button 
          icon={<EyeOutlined />} 
          size="small"
          onClick={() => {
            // View details modal would go here
            console.log('View details:', record);
          }}
        >
          Details
        </Button>
      ),
    },
  ];

  return (
    <Card 
      title="Agent History" 
      extra={
        <Space>
          <Select 
            value={agentFilter} 
            onChange={setAgentFilter} 
            style={{ width: 150 }}
          >
            <Option value="all">All Agents</Option>
            <Option value="task_agent">Task Agent</Option>
            <Option value="clock_agent">Clock Agent</Option>
            <Option value="report_agent">Report Agent</Option>
          </Select>
          
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            format="YYYY-MM-DD"
          />
        </Space>
      }
    >
      <Table 
        columns={columns} 
        dataSource={agentHistory || []} 
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

export default AgentHistory;