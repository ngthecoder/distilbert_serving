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
    const payload = { text: "The movie was a masterpiece of modern cinema. The director skillfully wove together multiple storylines, each character receiving careful development throughout the narrative. The cinematography was breathtaking, with every scene meticulously composed to evoke deep emotional responses from the audience. The musical score perfectly complemented the visuals, creating an immersive experience that lingered long after the credits rolled." }

    let res = http.post(url, JSON.stringify(payload), {
        headers: { 'Content-Type': 'application/json' },
    });

    console.log(res.json().label);
}
