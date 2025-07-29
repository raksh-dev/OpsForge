import React, { useState } from 'react';
import { Card, Button, Table, DatePicker, Space, message, Statistic, Row, Col } from 'antd';
import { ClockCircleOutlined, LoginOutlined, LogoutOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { employeeAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import moment from 'moment';

const { RangePicker } = DatePicker;

const Attendance = () => {
  const [dateRange, setDateRange] = useState([moment().startOf('month'), moment().endOf('month')]);
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: attendanceData, isLoading } = useQuery(
    ['attendance', dateRange],
    () => employeeAPI.getAttendance({
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD')
    })
  );

  const clockInMutation = useMutation(employeeAPI.clockIn, {
    onSuccess: () => {
      queryClient.invalidateQueries('attendance');
      message.success('Clocked in successfully');
    },
    onError: () => {
      message.error('Failed to clock in');
    }
  });

  const clockOutMutation = useMutation(employeeAPI.clockOut, {
    onSuccess: () => {
      queryClient.invalidateQueries('attendance');
      message.success('Clocked out successfully');
    },
    onError: () => {
      message.error('Failed to clock out');
    }
  });

  const handleClockIn = () => {
    clockInMutation.mutate();
  };

  const handleClockOut = () => {
    clockOutMutation.mutate();
  };

  const columns = [
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      render: (date) => moment(date).format('YYYY-MM-DD'),
    },
    {
      title: 'Clock In',
      dataIndex: 'clock_in',
      key: 'clock_in',
      render: (time) => time ? moment(time).format('HH:mm:ss') : '-',
    },
    {
      title: 'Clock Out',
      dataIndex: 'clock_out',
      key: 'clock_out',
      render: (time) => time ? moment(time).format('HH:mm:ss') : '-',
    },
    {
      title: 'Hours Worked',
      key: 'hours_worked',
      render: (_, record) => {
        if (record.clock_in && record.clock_out) {
          const duration = moment.duration(moment(record.clock_out).diff(moment(record.clock_in)));
          return `${Math.floor(duration.asHours())}h ${duration.minutes()}m`;
        }
        return '-';
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === 'present' ? 'green' : status === 'absent' ? 'red' : 'orange';
        return <span style={{ color }}>{status?.toUpperCase()}</span>;
      },
    },
  ];

  const todayRecord = attendanceData?.records?.find(record => 
    moment(record.date).isSame(moment(), 'day')
  );

  const totalHours = attendanceData?.records?.reduce((sum, record) => {
    if (record.clock_in && record.clock_out) {
      return sum + moment.duration(moment(record.clock_out).diff(moment(record.clock_in))).asHours();
    }
    return sum;
  }, 0) || 0;

  const presentDays = attendanceData?.records?.filter(record => record.status === 'present').length || 0;

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Today's Status"
              value={todayRecord?.status || 'Not Clocked In'}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Present Days"
              value={presentDays}
              suffix={`/ ${dateRange[1].diff(dateRange[0], 'days') + 1}`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Hours"
              value={totalHours.toFixed(1)}
              suffix="hrs"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space>
              <Button 
                type="primary" 
                icon={<LoginOutlined />}
                onClick={handleClockIn}
                loading={clockInMutation.isLoading}
                disabled={todayRecord?.clock_in}
              >
                Clock In
              </Button>
              <Button 
                type="default" 
                icon={<LogoutOutlined />}
                onClick={handleClockOut}
                loading={clockOutMutation.isLoading}
                disabled={!todayRecord?.clock_in || todayRecord?.clock_out}
              >
                Clock Out
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card 
        title="Attendance Records" 
        extra={
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            format="YYYY-MM-DD"
          />
        }
      >
        <Table 
          columns={columns} 
          dataSource={attendanceData?.records || []} 
          loading={isLoading}
          rowKey="date"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default Attendance;