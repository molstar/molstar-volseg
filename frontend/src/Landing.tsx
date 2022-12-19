import { useEffect, useState } from 'react';

const DocsLink = 'http://molstar.org/viewer-docs/volumes_and_segmentations/overview/';

const ViewerURL = 'https://molstar.org/viewer/';

export function LandingPage() {
    const today = new Date();

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
            <div className='five columns'>
                <video autoPlay controls loop style={{ maxHeight: '100%', maxWidth: '100%' }} width='450'>
                    <source src='img/intro.mp4' type='video/mp4' />
                </video>
            </div>
            <div className='seven columns'  style= {{ display: 'flex', alignItems: 'center' }}>
                <div style={{ textAlign: 'justify', margin: 5 }}>
                    Mol* Volumes & Segmentations (Mol*VS) is a <a href='https://doi.org/10.1093/nar/gkab314'>Mol* Viewer</a> extension which adds support for large scale volumetric data & their segmentations.
                    Building on the existing Mol* ecosystem, this extension allows seamless integration of biomolecular data from cellular to atomic scale. It provides the means to visualize 
                    large-scale volumetric and segmentation data from cryo-EM, light miscroscopy, volume-EM, and other imagining experiments together with related
                    3D model data and biological annotations. This website is free and open to all users and there is no login requirement.
                </div>
            </div>
        </div>

        <div style={{ borderTop: '1px solid #E0DDD4', margin: '30px 0' }} />

        <div className='row' style={{ textAlign: 'center', marginTop: 20 }}>
            <div className='twelve columns'>
                <h4 className='hero-heading' style={{ marginBottom: 30 }}><b>Interactive Examples</b></h4>
                {/* <div style={{ fontSize: '0.95rem', maxWidth: 500, margin: '10px auto 40px auto', color: '#555' }}>
                    WebGL2 support is required to view the interactive examples. The examples were tested in Firefox, Chrome & Safari on PC, Linux and MacOS/iOS.
                    Some users experienced rendering problems with integrated Intel graphics cards.
                </div> */}
                <div className='examples'>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('emd-1014.molj')}
                            target='_blank' rel='noreferrer'><img alt='EMD 1014' src='img/examples/emd-1014.png' /></a>
                        <p className='tooltip-info'>
                            <b><a href='https://www.ebi.ac.uk/emdb/EMD-1014' target='_blank' rel='noreferrer'>
                                EMD 1014
                            </a></b> showing 
                            combined EM/X-ray imaging yields a quasi-atomic model of the adenovirus-related bacteriophage PRD1 and key capsid and membrane interactions
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('empiar-10070.molj')} target='_blank' rel='noreferrer'><img 
                            alt='EMPIAR 10070' src='img/examples/ex-empiar-10070.png' /></a>
                        <p className='tooltip-info'>
                            <b><a href='https://www.ebi.ac.uk/empiar/EMPIAR-10070/' target='_blank' rel='noreferrer'>
                                EMPIAR 10070
                            </a></b> showing focused Ion Beam-Scanning Electron Microscopy of mitochondrial reticulum in murine skeletal muscle
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('idr-6001240.molj')}
                            target='_blank' rel='noreferrer'><img alt='IDR 6001240' src='img/examples/ex-idr-6001240.png' /></a>
                        <p className='tooltip-info'>
                            <a href='https://idr.openmicroscopy.org/webclient/img_detail/6001240/?dataset=7754' target='_blank' rel='noreferrer'>
                                IDR 6001240
                            </a> showcasing NGFF support
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('emd-9094.molj')}
                            target='_blank' rel='noreferrer'><img alt='EMD 9094' src='img/examples/emd-9094.png' /></a>
                        <p className='tooltip-info'>
                            <b><a href='https://www.ebi.ac.uk/emdb/EMD-9094' target='_blank' rel='noreferrer'>
                                EMD 9094
                            </a></b> showing 
                            Single-Molecule 3D Image of Two Human Plasma Intermediate-Density Lipoproteins in Complex with One Monoclonal Antibody MAB012 with Segmentations computed 
                            by <a href='https://bio3d.colorado.edu/imod/' target='_blank' rel='noreferrer'>IMOD</a> and <a href='https://www.cgl.ucsf.edu/chimera/docs/ContributedSoftware/segger/segment.html' target='_blank' rel='noreferrer'>Segger</a>.
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href={resolveExampleSnapshotURL('empiar-10819.molj')} target='_blank' rel='noreferrer'><img 
                            alt='EMPIAR 10819' src='img/examples/empiar-10819.png' /></a>
                        <p className='tooltip-info'>
                            <b><a href='https://www.ebi.ac.uk/empiar/EMPIAR-10819/' target='_blank' rel='noreferrer'>
                                EMPIAR 10819
                            </a></b> showing benchmark FIB SEM data of HeLa cells previously imaged by Zeiss LSM900 Airyscan microscopy
                            visualized using direct volumetric rendering
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div style={{ borderTop: '1px solid #E0DDD4', margin: '30px 0' }} />

        <div className='row' style={{ marginTop: 0, display: 'flex' }}>
            <div className='twelve columns'
                style= {{ textAlign: 'justify' }}>
                <a className='button button-primary' href={ViewerURL} style={{ fontSize: '2rem', width: '100%' }}
                    target='_blank' rel='noreferrer'>Open Mol* Viewer</a>
            </div>
        </div>

        <div className='row' style={{ marginTop: 10 }}>
            <div className='eight columns'
                style= {{ textAlign: 'justify' }}>
                As of {`${today.getDate()}/${today.getMonth() + 1}/${today.getFullYear()}`}, the Mol*VS internal database contains <EntryCount /> entries. 
                We are actively cooperating with teams from <a href='https://www.ebi.ac.uk/emdb/'>EMDB</a>, <a href='https://www.ebi.ac.uk/empiar/'>EMPIAR</a>, and <a href='https://www.ebi.ac.uk/bioimage-archive/'>BioImageArchive</a> to ensure that Mol*VS always contains the latest
                segmentation data available in these primary sources. If you encounter trouble with a specific entry, check our documentation, as
                some of the source data may contain errors or not show well using default settings. To report issues or give suggestions, please get in touch with us.
            </div>
            <div className='four columns' style={{ display: 'flex', alignItems: 'center' }}>
                <div>
                    <a className='button' href={DocsLink} style={{ fontSize: '2rem', width: '100%' }}
                        target='_blank' rel='noreferrer'>Documentation</a>
                    <a className='button' href='http://molstar.org/viewer-docs/volumes_and_segmentations/database-contents/' style={{ fontSize: '2rem', width: '100%' }}
                        target='_blank' rel='noreferrer'>Data Overview</a>
                    <a className='button' href='https://github.com/molstar/molstar-volseg/issues' style={{ fontSize: '2rem', width: '100%', marginBottom: 0 }}
                        target='_blank' rel='noreferrer'>Issues and Feedback</a>
                </div>
            </div>
        </div>

        <div style={{ borderTop: '1px solid #E0DDD4', margin: '30px 0' }} />

        <div className='row' style={{ display: 'flex' }}>
            <div className='four columns' style={{ display: 'flex', alignItems: 'center' }}>
                <div>
                    <a className='button button-primary' href='https://github.com/molstar/cellstar-volume-server/' style={{ fontSize: '2rem', width: '100%' }} target='_blank' rel='noreferrer'>
                        <svg width='14' height='14' style={{ marginRight: '0.75rem' }}><use href='#github-logo' /></svg>
                        GitHub
                    </a>
                    <a className='button' href='https://molstar.org/viewer-docs/volumes_and_segmentations/running-molstarvs-locally/' style={{ fontSize: '2rem', width: '100%', marginBottom: 0 }}
                        target='_blank' rel='noreferrer'>Running Mol*VS Locally</a>
                </div>
            </div>
            <div className='eight columns'
                style= {{ textAlign: 'justify', display: 'flex', alignItems: 'center' }}>
                Mol*VS is an open-source project with a permissive MIT license.<br/>
                Do you have volume or mesh segmentation data that you wish to visualize before/without submission to a public database? You can do so by running an independent instance of Mol* with the Volumes and Segmentations extension.
            </div>
        </div>

        <div style={{ borderTop: '1px solid #E0DDD4', margin: '30px 0' }} />

        <div className='row' style={{ textAlign: 'right', color: '#999' }}>
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

function resolveExampleSnapshotURL(snapshot: string) {
    const snapshotRoot = `${window.location.origin}/snapshots/`;
    // const snapshotRoot = 'https://molstarvolseg.ncbr.muni.cz/snapshots/';
    return `${ViewerURL}?snapshot-url=${encodeURIComponent(`${snapshotRoot}${snapshot}`)}&snapshot-url-type=molj&prefer-webgl1=1`;
}

function EntryCount() {
    const [count, setCount] = useState<any>('...');
    useEffect(() => {
        fetch('https://molstarvolseg.ncbr.muni.cz/v2/list_entries/10000')
            .then(res => res.json())
            .then(res => {
                let count = 0;
                for (const xs of Array.from(Object.values(res))) count += (xs as any).length ?? 0;
                setCount(count);
            })
            .catch(err => {
                console.log(err);
            });
    });

    return <>{count}</>;
}