import React, { useState } from 'react';
import { Table, Card, Button, Tag, Space, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { employeeAPI } from '../services/api';

const { Option } = Select;

const Employees = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: employees, isLoading } = useQuery('employees', employeeAPI.getEmployees);

  const createMutation = useMutation(employeeAPI.createEmployee, {
    onSuccess: () => {
      queryClient.invalidateQueries('employees');
      message.success('Employee created successfully');
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: () => {
      message.error('Failed to create employee');
    }
  });

  const updateMutation = useMutation(employeeAPI.updateEmployee, {
    onSuccess: () => {
      queryClient.invalidateQueries('employees');
      message.success('Employee updated successfully');
      setIsModalVisible(false);
      setEditingEmployee(null);
      form.resetFields();
    },
    onError: () => {
      message.error('Failed to update employee');
    }
  });

  const deleteMutation = useMutation(employeeAPI.deleteEmployee, {
    onSuccess: () => {
      queryClient.invalidateQueries('employees');
      message.success('Employee deleted successfully');
    },
    onError: () => {
      message.error('Failed to delete employee');
    }
  });

  const handleSubmit = (values) => {
    if (editingEmployee) {
      updateMutation.mutate({ id: editingEmployee.id, ...values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleEdit = (employee) => {
    setEditingEmployee(employee);
    form.setFieldsValue(employee);
    setIsModalVisible(true);
  };

  const handleDelete = (employeeId) => {
    Modal.confirm({
      title: 'Are you sure you want to delete this employee?',
      onOk: () => deleteMutation.mutate(employeeId),
    });
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Department',
      dataIndex: 'department',
      key: 'department',
      render: (department) => department || '-',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const color = role === 'admin' ? 'red' : role === 'manager' ? 'blue' : 'green';
        return <Tag color={color}>{role.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Button icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} danger />
        </Space>
      ),
    },
  ];

  return (
    <Card 
      title="Employees" 
      extra={
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={() => setIsModalVisible(true)}
        >
          Add Employee
        </Button>
      }
    >
      <Table 
        columns={columns} 
        dataSource={employees} 
        loading={isLoading}
        rowKey="id"
      />

      <Modal
        title={editingEmployee ? 'Edit Employee' : 'Add Employee'}
        visible={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingEmployee(null);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="full_name"
            label="Full Name"
            rules={[{ required: true, message: 'Please enter full name' }]}
          >
            <Input prefix={<UserOutlined />} />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter email' },
              { type: 'email', message: 'Please enter valid email' }
            ]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter username' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="department"
            label="Department"
          >
            <Select placeholder="Select Department">
              <Option value="IT">IT</Option>
              <Option value="HR">HR</Option>
              <Option value="Finance">Finance</Option>
              <Option value="Marketing">Marketing</Option>
              <Option value="Operations">Operations</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Please select role' }]}
          >
            <Select>
              <Option value="employee">Employee</Option>
              <Option value="manager">Manager</Option>
              <Option value="admin">Admin</Option>
            </Select>
          </Form.Item>

          {!editingEmployee && (
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password />
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={createMutation.isLoading || updateMutation.isLoading}>
                {editingEmployee ? 'Update' : 'Create'}
              </Button>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default Employees;