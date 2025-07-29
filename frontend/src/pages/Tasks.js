import React, { useState } from 'react';
import { Table, Card, Button, Tag, Space, Modal, Form, Input, Select, DatePicker, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { taskAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import moment from 'moment';

const { Option } = Select;
const { TextArea } = Input;

const Tasks = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [form] = Form.useForm();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: tasks, isLoading } = useQuery('tasks', taskAPI.getTasks);

  const createMutation = useMutation(taskAPI.createTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      message.success('Task created successfully');
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: () => {
      message.error('Failed to create task');
    }
  });

  const updateMutation = useMutation(taskAPI.updateTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      message.success('Task updated successfully');
      setIsModalVisible(false);
      setEditingTask(null);
      form.resetFields();
    },
    onError: () => {
      message.error('Failed to update task');
    }
  });

  const deleteMutation = useMutation(taskAPI.deleteTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      message.success('Task deleted successfully');
    },
    onError: () => {
      message.error('Failed to delete task');
    }
  });

  const handleSubmit = (values) => {
    const taskData = {
      ...values,
      due_date: values.due_date?.toISOString(),
    };

    if (editingTask) {
      updateMutation.mutate({ id: editingTask.id, ...taskData });
    } else {
      createMutation.mutate(taskData);
    }
  };

  const handleEdit = (task) => {
    setEditingTask(task);
    form.setFieldsValue({
      ...task,
      due_date: task.due_date ? moment(task.due_date) : null,
    });
    setIsModalVisible(true);
  };

  const handleDelete = (taskId) => {
    Modal.confirm({
      title: 'Are you sure you want to delete this task?',
      onOk: () => deleteMutation.mutate(taskId),
    });
  };

  const columns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const color = status === 'completed' ? 'green' : status === 'in_progress' ? 'blue' : 'orange';
        return <Tag color={color}>{status.replace('_', ' ').toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => {
        const color = priority === 'high' ? 'red' : priority === 'medium' ? 'orange' : 'green';
        return <Tag color={color}>{priority.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Assigned To',
      dataIndex: 'assigned_to_name',
      key: 'assigned_to_name',
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due_date',
      render: (date) => date ? moment(date).format('YYYY-MM-DD') : '-',
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
      title="Tasks" 
      extra={
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={() => setIsModalVisible(true)}
        >
          Add Task
        </Button>
      }
    >
      <Table 
        columns={columns} 
        dataSource={tasks} 
        loading={isLoading}
        rowKey="id"
      />

      <Modal
        title={editingTask ? 'Edit Task' : 'Add Task'}
        visible={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingTask(null);
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
            name="title"
            label="Title"
            rules={[{ required: true, message: 'Please enter task title' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={4} />
          </Form.Item>

          <Form.Item
            name="status"
            label="Status"
            rules={[{ required: true, message: 'Please select status' }]}
          >
            <Select>
              <Option value="pending">Pending</Option>
              <Option value="in_progress">In Progress</Option>
              <Option value="completed">Completed</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="priority"
            label="Priority"
            rules={[{ required: true, message: 'Please select priority' }]}
          >
            <Select>
              <Option value="low">Low</Option>
              <Option value="medium">Medium</Option>
              <Option value="high">High</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="due_date"
            label="Due Date"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={createMutation.isLoading || updateMutation.isLoading}>
                {editingTask ? 'Update' : 'Create'}
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

export default Tasks;