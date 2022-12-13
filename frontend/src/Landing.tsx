export function LandingPage() {
    return <div className='container' style={{ marginBottom: 20 }}>
        <div className='row' style={{ textAlign: 'center', marginTop: 40 }}>
            <img style={{ maxWidth: 160, width: '100%', marginBottom: 20 }} src='img/molstar-logo.png' alt='logo' />
            <h2 style={{ fontWeight: 'bold' }}>
                Volumes & Segmentations
            </h2>
        </div>

        <div className='row' style={{ textAlign: 'center' }}>
            <div className='two columns'>&nbsp;</div>
            <div className='eight columns' style={{ borderTop: '1px solid #E0DDD4', paddingTop: 20 }}>
                <h5 className='hero-heading'>
                    A <a href='https://molstar.org' target='_blank' rel='noreferrer'>Mol*</a> extension with support for large-scale volumetric data and segmentations
                </h5>
            </div>
            <div className='two columns'>&nbsp;</div>
        </div>

        <div className='row' style={{ marginTop: 0, display: 'flex' }}>
            <div className='twelve column'
                style= {{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                <a href={resolveExampleSnapshotURL('emd-1181.molj')} target='_blank' rel='noreferrer' title='Open Mol* Viewer'>
                    <video autoPlay controls loop style={{ maxHeight: '100%', maxWidth: '100%' }} width='450'>
                        <source src='/img/2C7D_state-snapshots.mp4' type='video/mp4' />
                    </video>
                </a>

                <div style={{ textAlign: 'center', margin: 5 }}>
                    Mol* Volumes & Segmentations is a Mol* extension which adds the support for large scale volumetric data & their segmentations. Building on the existing Mol* ecosystem, the extension
                    allows seamless integration of biomolecular data ranging from whole cell 3D reconstructions from light miscroscopy, all the way down to atomic level.
                </div>
            </div>
        </div>

        <div className='row' style={{ textAlign: 'center', marginTop: 20 }}>
            <div className='twelve columns'>
                <h4 className='hero-heading' style={{ marginBottom: 0 }}><b>Interactive Examples</b></h4>
                <div style={{ fontSize: '0.95rem', maxWidth: 500, margin: '10px auto 40px auto', color: '#555' }}>
                    WebGL2 support is required to view the interactive examples. The examples were tested in Firefox, Chrome & Safari on PC, Linux and MacOS/iOS.
                    Some users experienced rendering problems with integrated Intel graphics cards.
                </div>
                <div className='examples'>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('emd-1181.molj')}
                            target='_blank' rel='noreferrer'><img alt='EMD 1181' src='img/examples/ex-emd-1181.png' /></a>
                        <p className='tooltip-info'>
                            <a href='https://www.ebi.ac.uk/emdb/EMD-1181' target='_blank' rel='noreferrer'>
                                EMD 1181
                            </a>
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('empiar-10070.molj')} target='_blank' rel='noreferrer'><img 
                            alt='EMPIAR 10070' src='img/examples/ex-empiar-10070.png' /></a>
                        <p className='tooltip-info'>
                            <a href='https://www.ebi.ac.uk/empiar/EMPIAR-10070/' target='_blank' rel='noreferrer'>
                                EMPIAR 10070
                            </a>
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('idr-6001240.molj')}
                            target='_blank' rel='noreferrer'><img alt='Zika+EM' src='img/examples/ex-idr-6001240.png' /></a>
                        <p className='tooltip-info'>
                            <a href='https://idr.openmicroscopy.org/webclient/img_detail/6001240/?dataset=7754' target='_blank' rel='noreferrer'>
                                IDR 6001240
                            </a> (experimental NGFF support)
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div className='row' style={{ marginTop: 60, display: 'flex' }}>
            <div className='twelve columns'
                style= {{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                {/* <a className='button button-primary' href='https://github.com/molstar/cellstar-volume-server/' style={{ fontSize: '2rem', width: '100%' }} target='_blank' rel='noreferrer'>
                    <svg width='14' height='14' style={{ marginRight: '0.75rem' }}><use href='#github-logo' /></svg>
                    GitHub
                </a> */}
                <a className='button' href={ViewerURL} style={{ fontSize: '2rem', width: '100%' }}
                    target='_blank' rel='noreferrer'>Open Mol* Viewer</a>
            </div>
        </div>

        <div className='row' style={{ textAlign: 'center', marginTop: 20 }}>
            <div className='twelve columns'>
                {/* <h4 className='hero-heading' style={{ marginBottom: 40 }}><b>Quick Tutorial</b></h4> */}

                <video controls loop style={{ maxHeight: '100%', maxWidth: '100%' }} width='550'>
                    <source src='/img/quick-tutorial.mp4' type='video/mp4' />
                </video>
            </div>
        </div>

        <div className='row' style={{ textAlign: 'right', marginTop: 60, color: '#999' }}>
            Copyright 2022–now, Mol* Volumes & Segmentations Contributors | <a href='terms-of-use.html' style={{ color: '#999' }}>Terms of Use &
                GDPR</a>
        </div>

        <svg style={{ display: 'none' }} version='2.0'>
            <defs>
                <symbol id='github-logo' viewBox='0 0 24 24'>
                    <path d='M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z' />
                </symbol>
            </defs>
        </svg>
    </div>
}

const ViewerURL = 'https://overprot.ncbr.muni.cz/data/cellstar/';

function resolveExampleSnapshotURL(snapshot: string) {
    const snapshotRoot = `${window.location.origin}/snapshots/`;
    return `${ViewerURL}?snapshot-url=${encodeURIComponent(`${snapshotRoot}${snapshot}`)}&snapshot-url-type=molj`;
}