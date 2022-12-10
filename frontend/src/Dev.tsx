import { lazy, Suspense } from 'react';

const Viewer = lazy(() => import('./DevViewer'));

export function DevViewerWrapper() {
    return <Suspense fallback='Loading...'>
        <Viewer />
    </Suspense>;
}