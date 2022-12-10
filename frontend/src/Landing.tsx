export function LandingPage() {
    return <div className='container' style={{ marginBottom: 20 }}>
        {/* <div className='row' style={{ textAlign: 'center', marginTop: 40, fontWeight: 'bold' }}>
            <img style={{ maxWidth: 160, width: '100%' }} src='img/molstar-logo.png' alt='logo' />
        </div> */}
        <div className='row' style={{ textAlign: 'center', marginTop: 40 }}>
            <img style={{ maxWidth: 160, width: '100%', marginBottom: 20 }} src='img/molstar-logo.png' alt='logo' />
            <h2 style={{ fontWeight: 'bold' }}>
                Cell* Volumes & Segmentations
            </h2>
        </div>

        <div className='row' style={{ textAlign: 'center' }}>
            <div className='two columns'>&nbsp;</div>
            <div className='eight columns' style={{ borderTop: '1px solid #E0DDD4', paddingTop: 20 }}>
                <h5 className='hero-heading'>
                    Cell* (<i>/'cellstar/</i>) is a <a href='https://molstar.org' target='_blank' rel='noreferrer'>Mol*</a> extension focused on support for large-scale volumetric data and segmentations
                </h5>
            </div>
            <div className='two columns'>&nbsp;</div>
        </div>

        {/* <div className='row'>
            <div className='twelve columns' style={{ textAlign: 'center' }}>
                <video controls autoPlay loop width='250'>
                    <source src='/img/animation.mp4' type='video/mp4' />
                </video>
            </div>
        </div> */}

        <div className='row' style={{ marginTop: 30, display: 'flex' }}>
            <div className='one-half column'
                style= {{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                <a href='viewer' target='_blank' title='Open Mol* Viewer'>
                    <video controls autoPlay loop style={{ maxHeight: '100%', maxWidth: '100%' }} width='320'>
                        <source src='/img/2C7D_state-snapshots.mp4' type='video/mp4' />
                    </video>
                </a>
            </div>
            <div className='one-half column'
                style= {{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                <a className='button button-primary' href='viewer' style={{ fontSize: '2rem', width: '100%' }}
                    target='_blank'>Open Mol* Viewer</a>
                <a className='button' href='https://github.com/molstar/cellstar-volume-server/' style={{ fontSize: '2rem', width: '100%' }} target='_blank' rel='noreferrer'>
                    <svg width='14' height='14' style={{ marginRight: '0.75rem' }}><use href='#github-logo' /></svg>
                    GitHub
                </a>
                {/* <a className='button' href='https://github.com/molstar/molstar/issues' style='font-size: 2rem; width: 100%;'
                    target='_blank'>Issues &amp; Feedback</a> */}
                <div style={{ textAlign: 'justify', margin: 5 }}>
                    Cell* Volumes & Segmentations is a Mol* extension which adds the support for large scale volumetric data & their segmentations. Building on the existing Mol* ecosystem, Cell* 
                    allows seamless integration of biomolecular data ranging from whole cell 3D reconstructions from light miscroscopy all the way down to atomic scale.
                </div>
            </div>
        </div>

        <div className='row' style={{ textAlign: 'center', marginTop: 40 }}>
            <div className='twelve columns'>
                <h4 className='hero-heading' style={{ marginBottom: 40 }}><b>Interactive Examples</b></h4>
                <div className='examples'>
                    <div className='tooltip'>
                        <a href='https://molstar.org/viewer/?snapshot-url=https%3A%2F%2Fmolstar.org%2Fdemos%2Fstates%2Fhiv-simple-cut.molx&snapshot-url-type=molx'
                            target='_blank'><img alt='HIV in blood serum' src='img/examples/e1.png' /></a>
                        <p className='tooltip-info'>
                            CellPack model of enveloped HIV capsid with ~13M atoms.
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href='demos/alpha-orbitals' target='_blank'><img
                                alt='Alpha orbitals and density of Atorvastatin' src='img/examples/e2.png' /></a>
                        <p className='tooltip-info'>
                            Alpha orbitals and density of Atorvastatin.
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href='https://molstar.org/viewer/?snapshot-url=https%3A%2F%2Fmolstar.org%2Fdemos%2Fstates%2Fzikaem.molx&snapshot-url-type=molx'
                            target='_blank'><img alt='Zika+EM' src='img/examples/e3.png' /></a>
                        <p className='tooltip-info'>
                            Zika virus assembly and Cryo-EM density.
                        </p>
                    </div>
                    <div className='tooltip'>
                        <a href='https://molstar.org/viewer/?snapshot-url=https%3A%2F%2Fmolstar.org%2Fdemos%2Fstates%2Fcytochromes.molx&snapshot-url-type=molx'
                            target='_blank'><img alt='P-450 Superposition' src='img/examples/e4.png' /></a>
                        <p className='tooltip-info'>
                            Superposition and validation annotation of P-450 cytochromes.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div className='row' style={{ textAlign: 'right', marginTop: 60, color: '#999' }}>
            Copyright 2022–now, Cell* Contributors | <a href='terms-of-use.html' style={{ color: '#999' }}>Terms of Use &
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