import http from 'k6/http';

export const options = {
    scenarios: {
        contacts: {
            executor: 'constant-vus',
            vus: 10,
            duration: '120s',
        },
    },
};

const url = 'http://<LOAD_BALANCER_URL>:8080/analyze';

export default function () {
    const payload = { text: "The film had great acting and an engaging plot." }

    let res = http.post(url, JSON.stringify(payload), {
        headers: { 'Content-Type': 'application/json' },
    });

    console.log(res.json().label);
}
