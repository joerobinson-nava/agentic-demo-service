pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }
        stage('Lint') {
            steps {
                sh '''
                    . .venv/bin/activate
                    ruff check .
                '''
            }
        }
        stage('Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -q
                '''
            }
        }
        stage('Security') {
            steps {
                sh '''
                    . .venv/bin/activate
                    bandit -r app -ll
                '''
            }
        }
    }
}
