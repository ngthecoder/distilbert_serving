import http from 'k6/http';

export const options = {
    scenarios: {
        contacts: {
            executor: 'constant-vus',
            vus: 10,
            duration: '30s',
        },
    },
};

const url = 'http://a0e07c34464164758ac9f1c05784300b-1532965653.us-east-1.elb.amazonaws.com:8080/analyze';

export default function () {
    let data = { text: 'I lost my wallet.' };

    let res = http.post(url, JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    console.log(res.json().label);
}