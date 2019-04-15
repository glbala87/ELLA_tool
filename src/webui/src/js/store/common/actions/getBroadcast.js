export default async function getBroadcast({ http, path }) {
    try {
        const result = await http.get(`broadcasts/`)
        return path.success(result)
    } catch (error) {
        console.log(error)
        return path.error(error)
    }
}
