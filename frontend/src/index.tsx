import React from 'react';
import ReactDOM from 'react-dom';  // React17
// import {createRoot} from 'react-dom/client';  // React18
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

ReactDOM.render(  // React17
    <React.StrictMode>
        <App />
    </React.StrictMode>,
    document.getElementById('root')
);
// createRoot(document.getElementById('root')!).render(  // React18
//     <React.StrictMode>
//         <App />
//     </React.StrictMode>
// );

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
