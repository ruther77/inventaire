import Stepper from './Stepper.jsx';

export default {
  title: 'newCMS/Stepper',
  component: Stepper,
};

export const Default = {
  args: {
    steps: ['Upload', 'Validation', 'Confirmation'],
    active: 1,
  },
};
