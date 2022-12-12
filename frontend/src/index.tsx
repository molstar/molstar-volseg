import React from 'react';
import ReactDOM from 'react-dom';  // React17
import { DevViewerWrapper } from './Dev';
// import {createRoot} from 'react-dom/client';  // React18
import './index.css';
import { LandingPage } from './Landing';

console.log(window.location.pathname)

if (window.location.pathname.indexOf('/dev') === 0) {
    ReactDOM.render(  // React17
        <React.StrictMode>
            <DevViewerWrapper />
        </React.StrictMode>,
        document.getElementById('root')
    );
} else {
    ReactDOM.render(  // React17
        <React.StrictMode>
            <LandingPage />
        </React.StrictMode>,
        document.getElementById('root')
    );
}
// createRoot(document.getElementById('root')!).render(  // React18
//     <React.StrictMode>
//         <App />
//     </React.StrictMode>
// );

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// reportWebVitals();
