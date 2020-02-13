function getConfig({ http, path }) {
    return http.get(`config`).then((response) => {
        if (response.status === 200) {
            return path.success({ result: response.result })
        }
        return path.error({ result: response.result })
    })
}

export default getConfig
