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
    const payload = { text: "I thought I failed the exam but unexpectedly the score was 92% when the average was 60%!" }

    let res = http.post(url, JSON.stringify(payload), {
        headers: { 'Content-Type': 'application/json' },
    });

    console.log(res.json().label);
}
