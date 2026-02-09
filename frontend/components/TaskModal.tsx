'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Task } from '@/lib/api';
import { toast } from 'sonner';
import TaskForm, { TaskFormData } from '@/components/TaskForm';

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: Task | undefined;
  onCreateTask: (data: TaskFormData) => Promise<Task | null>;
  onUpdateTask: (id: string, data: TaskFormData) => Promise<Task | null>;
}

export default function TaskModal({ isOpen, onClose, task, onCreateTask, onUpdateTask }: TaskModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSave = async (formData: TaskFormData) => {
    setIsSubmitting(true);
    try {
      if (task) {
        const updatedTask = await onUpdateTask(task.id, formData);
        if (updatedTask) {
          onClose();
        } else {
          toast.error('Failed to update task');
        }
      } else {
        const newTask = await onCreateTask(formData);
        if (newTask) {
          onClose();
        } else {
          toast.error('Failed to create task');
        }
      }
    } catch (error) {
      console.error('Error saving task:', error);
      toast.error(task ? 'Failed to update task' : 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setIsSubmitting(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md md:max-w-lg lg:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{task ? 'Edit Task' : 'Create New Task'}</DialogTitle>
        </DialogHeader>

        <TaskForm
          task={task}
          onSubmit={handleSave}
          onCancel={handleCancel}
          isSubmitting={isSubmitting}
        />
      </DialogContent>
    </Dialog>
  );
}
