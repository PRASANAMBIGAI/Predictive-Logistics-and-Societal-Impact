import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// Your actual Firebase web app config object
const firebaseConfig = {
    apiKey: "AIzaSyCxut3Z5La0ECSF191C-eezoDFHHjEuOgw",
    authDomain: "predictive-logistics-f09cc.firebaseapp.com",
    projectId: "predictive-logistics-f09cc",
    storageBucket: "predictive-logistics-f09cc.firebasestorage.app",
    messagingSenderId: "1024546130488",
    appId: "1:1024546130488:web:f8272db655656389ccb4cd",
    measurementId: "G-FW0TWYY38T"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Cloud Firestore and get a reference to the service
const db = getFirestore(app);

export { app, db };
