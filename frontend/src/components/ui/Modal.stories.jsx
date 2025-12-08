import { useState } from 'react';
import Modal from './Modal';
import Button from './Button';

export default {
  title: 'UI/Modal',
  component: Modal,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

const ModalDemo = ({ title, children }) => {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal open={open} onClose={() => setOpen(false)} title={title}>
        {children}
      </Modal>
    </>
  );
};

export const Default = {
  render: () => (
    <ModalDemo title="Example Modal">
      <p className="text-slate-600">
        This is a modal dialog. Click outside or press Escape to close.
      </p>
    </ModalDemo>
  ),
};

export const WithActions = {
  render: () => (
    <ModalDemo title="Confirm Action">
      <div className="space-y-4">
        <p className="text-slate-600">
          Are you sure you want to proceed with this action?
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost">Cancel</Button>
          <Button variant="brand">Confirm</Button>
        </div>
      </div>
    </ModalDemo>
  ),
};

export const LongContent = {
  render: () => (
    <ModalDemo title="Terms and Conditions">
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {Array.from({ length: 10 }).map((_, i) => (
          <p key={i} className="text-slate-600">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
            eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
            ad minim veniam, quis nostrud exercitation ullamco laboris.
          </p>
        ))}
      </div>
    </ModalDemo>
  ),
};
