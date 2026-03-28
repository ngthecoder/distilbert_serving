import http from 'k6/http';

export const options = {
    scenarios: {
        spike: {
            executor: 'ramping-vus',
            stages: [
                { duration: '10s', target: 1 },
                { duration: '5s', target: 40 },
                { duration: '30s', target: 40 },
                { duration: '10s', target: 1 },
            ],
        },
    },
};

const url = 'http://af6076ec46df3438b9474c35a3f52f62-1584184945.us-east-1.elb.amazonaws.com:8080/analyze';

export default function () {
    let data = { text: 'I lost my wallet.' };

    let res = http.post(url, JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    console.log(res.json().label);
}