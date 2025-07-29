import React, { useState } from 'react';
import { Card, Table, DatePicker, Select, Button, Space } from 'antd';
import { DownloadOutlined, FileExcelOutlined } from '@ant-design/icons';
import { useQuery } from 'react-query';
import { employeeAPI } from '../services/api';
import moment from 'moment';

const { RangePicker } = DatePicker;
const { Option } = Select;

const Reports = () => {
  const [reportType, setReportType] = useState('attendance');
  const [dateRange, setDateRange] = useState([moment().startOf('month'), moment().endOf('month')]);

  const { data: reportData, isLoading } = useQuery(
    ['reports', reportType, dateRange],
    () => employeeAPI.getReports({
      type: reportType,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD')
    }),
    { enabled: !!reportType && !!dateRange }
  );

  const attendanceColumns = [
    {
      title: 'Employee',
      dataIndex: 'employee_name',
      key: 'employee_name',
    },
    {
      title: 'Present Days',
      dataIndex: 'present_days',
      key: 'present_days',
    },
    {
      title: 'Absent Days',
      dataIndex: 'absent_days',
      key: 'absent_days',
    },
    {
      title: 'Total Hours',
      dataIndex: 'total_hours',
      key: 'total_hours',
      render: (hours) => `${hours}h`,
    },
    {
      title: 'Attendance Rate',
      dataIndex: 'attendance_rate',
      key: 'attendance_rate',
      render: (rate) => `${rate}%`,
    },
  ];

  const taskColumns = [
    {
      title: 'Employee',
      dataIndex: 'employee_name',
      key: 'employee_name',
    },
    {
      title: 'Completed Tasks',
      dataIndex: 'completed_tasks',
      key: 'completed_tasks',
    },
    {
      title: 'Pending Tasks',
      dataIndex: 'pending_tasks',
      key: 'pending_tasks',
    },
    {
      title: 'In Progress',
      dataIndex: 'in_progress_tasks',
      key: 'in_progress_tasks',
    },
    {
      title: 'Completion Rate',
      dataIndex: 'completion_rate',
      key: 'completion_rate',
      render: (rate) => `${rate}%`,
    },
  ];

  const getColumns = () => {
    switch (reportType) {
      case 'attendance':
        return attendanceColumns;
      case 'tasks':
        return taskColumns;
      default:
        return attendanceColumns;
    }
  };

  const handleExport = () => {
    // Implement export functionality
    console.log('Exporting report...');
  };

  return (
    <Card 
      title="Reports" 
      extra={
        <Space>
          <Button 
            icon={<FileExcelOutlined />} 
            onClick={handleExport}
          >
            Export Excel
          </Button>
          <Button 
            type="primary" 
            icon={<DownloadOutlined />} 
            onClick={handleExport}
          >
            Download PDF
          </Button>
        </Space>
      }
    >
      <Space style={{ marginBottom: 16 }}>
        <Select 
          value={reportType} 
          onChange={setReportType} 
          style={{ width: 200 }}
        >
          <Option value="attendance">Attendance Report</Option>
          <Option value="tasks">Task Report</Option>
          <Option value="performance">Performance Report</Option>
        </Select>
        
        <RangePicker
          value={dateRange}
          onChange={setDateRange}
          format="YYYY-MM-DD"
        />
      </Space>

      <Table 
        columns={getColumns()} 
        dataSource={reportData || []} 
        loading={isLoading}
        rowKey="employee_id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

export default Reports;