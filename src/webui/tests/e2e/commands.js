const { execSync, spawnSync } = require('child_process')

function waitForCerebral() {
    try {
        browser.setTimeout({ script: 10000 })
        browser.executeAsync(function(done) {
            const MAX_WAIT = 1000
            const CHECK_INTERVAL = 10

            // See code for exception handling to see how window.__cerebralRunningSignals is implemented.

            let checkCnt = 0
            const checkInterval = window.setInterval(
                () => {
                    checkCnt += 1
                    // Timeout: some signals can running stay for a long time by design, we don't want to wait for those
                    if (
                        ('__cerebralRunningSignals' in window &&
                            window.__cerebralRunningSignals.length) === 0 ||
                        checkCnt > MAX_WAIT / CHECK_INTERVAL
                    ) {
                        window.clearInterval(checkInterval)
                        done()
                    }
                },
                CHECK_INTERVAL,
                false
            )
            if (
                '__cerebralRunningSignals' in window &&
                window.__cerebralRunningSignals.length === 0
            ) {
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
    let result = spawnSync('psql', [process.env.DB_URL, '-c', sql])
    if (result.status != 0) {
        throw Error(result.stderr.toString('utf8'))
    }
    return result.stdout.toString('utf8')
}

function addCommands() {
    browser.addCommand('resetDb', () => {
        console.log(`Resetting database with 'e2e' (this can take a while...)`)
        execSync(`ella-cli database drop -f`, {
            stdio: ['ignore', 'ignore', 'pipe']
        })

        execSync(`/ella/ops/testdata/reset-testdata.py reset --testset e2e`, {
            stdio: ['ignore', 'ignore', 'pipe']
        })
        console.log('Database reset from dump done!')
    })

    browser.addCommand('setWysiwygValue', (editorSelector, editorWysiwygSelector, value) => {
        // HACK: In Chrome/chromedriver 78 the focus logic of webdriver command 'clear element'
        // changed, so our wysiwyg editor loses focus. This code splits setValue() into their
        // individual commands and refocuses the editor in-between.
        $(editorSelector).click()
        browser.pause(500)
        const elemId = Object.values(browser.findElement('css selector', editorWysiwygSelector))[0]
        browser.elementClear(elemId)
        browser.pause(500)
        $(editorSelector).click()
        $(editorWysiwygSelector).addValue(value)
        browser.pause(50)
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
