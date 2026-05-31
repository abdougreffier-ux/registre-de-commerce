import React from 'react';
import ReactDOM from 'react-dom/client';
import 'antd/dist/reset.css';

// Charte graphique officielle RIM — DOIT être importée après Ant Design
// pour que ses surcharges prennent effet.
import './charte/charte.css';

import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
