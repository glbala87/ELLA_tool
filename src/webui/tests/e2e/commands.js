const { execSync, spawnSync } = require('child_process')

function waitForCerebral() {
    try {
        browser.setTimeout({ script: 10000 })
        browser.executeAsync(function(done) {
            const MAX_WAIT = 1000
            const CHECK_INTERVAL = 10

            // use 'window.'' to work around weird bug when testing for undefined..
            if (!('__cerebralRunningSignals' in window)) {
                if (window.angular) {
                    window.__cerebralRunningSignals = 0
                    const cerebral = angular
                        .element(document.body)
                        .injector()
                        .get('cerebral')
                    cerebral.controller.on('start', (execution, payload) => {
                        window.__cerebralRunningSignals += 1
                    })
                    cerebral.controller.on('end', (execution, payload) => {
                        window.__cerebralRunningSignals -= 1
                        // If we were injected too late, we might have missed a few start events
                        // This can make counter go negative
                        if (window.__cerebralRunningSignals < 0) {
                            window.__cerebralRunningSignals = 0
                        }
                    })
                } else {
                    done()
                    return
                }
            }
            let checkCnt = 0
            const checkInterval = window.setInterval(
                () => {
                    checkCnt += 1
                    // Timeout: some signals can running stay for a long time by design, we don't want to wait for those
                    if (
                        window.__cerebralRunningSignals === 0 ||
                        checkCnt > MAX_WAIT / CHECK_INTERVAL
                    ) {
                        window.clearInterval(checkInterval)
                        done()
                    }
                },
                CHECK_INTERVAL,
                false
            )
            if (window.__cerebralRunningSignals === 0) {
                window.clearInterval(checkInterval)
                done()
                return
            }
        })
    } catch (err) {
        // Hack: Work around page changes interrupting script after switching to page.js
        // Any logic around page changes should use waitFor rather than wait for Cerebral anyways
        if (err.message !== 'javascript error: document unloaded while waiting for result') {
            throw err
        }
    }
}

function psql(sql) {
    let result = spawnSync('psql', ['postgres', '-c', sql])
    if (result.status != 0) {
        throw Error(result.stderr.toString('utf8'))
    }
    return result.stdout.toString('utf8')
}

function addCommands() {
    browser.addCommand('resetDb', (testset = 'e2e') => {
        console.log(`Resetting database with '${testset}' (this can take a while...)`)
        try {
            execSync(`ella-cli database drop -f`, {
                stdio: ['ignore', 'ignore', 'pipe']
            })
            execSync(`psql postgres < /ella/dbdump_${testset}.sql`, {
                stdio: ['ignore', 'ignore', 'pipe']
            })
            console.log('Database reset from dump done!')
        } catch (err) {
            execSync(`make -C /ella dbreset TESTSET=${testset}`, {
                stdio: ['ignore', 'ignore', 'pipe']
            })
            execSync(`pg_dump postgres > /ella/dbdump_${testset}.sql`)
            console.log('Database reset done!')
        }
    })

    browser.addCommand('psql', psql)
    browser.addCommand('getClass', (selector) =>
        $(selector)
            .getAttribute('class')
            .split(' ')
    )
    browser.addCommand('isCommentEditable', (selector) => {
        let res = $(selector).getAttribute('contenteditable')
        return res === 'true'
    })
}

module.exports = {
    waitForCerebral,
    addCommands
}
