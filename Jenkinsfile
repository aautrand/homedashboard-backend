pipeline {
    agent any

    parameters {
        string(name: 'VERSION', description: 'New version to release (e.g. 1.4.2)', trim: true)
    }

    // NEXUS_REGISTRY (host:port) and FORGEJO_HOST come from Jenkins global
    // environment variables, so no internal addresses live in the repo.
    environment {
        IMAGE = 'homedashboard-be'
    }

    stages {
        stage('Validate') {
            steps {
                script {
                    if (!params.VERSION?.trim()) {
                        error('VERSION parameter is required')
                    }
                }
            }
        }

        stage('Security') {
            steps {
                sh 'pip3 install bandit && python3 -m bandit -c bandit.yaml -r dashboard/'
            }
        }

        stage('Version') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'forgejo-token',
                                                   usernameVariable: 'GIT_USER',
                                                   passwordVariable: 'GIT_PASS')]) {
                    sh """
                        echo ${params.VERSION} > version
                        git config user.email "jenkins@home"
                        git config user.name "Jenkins"
                        git add version
                        git commit -m "[system] Bump version to ${params.VERSION}" || true
                        git push http://\$GIT_USER:\$GIT_PASS@\$FORGEJO_HOST/aautrand/homedashboard-be.git HEAD:dev
                    """
                }
            }
        }

        stage('Build') {
            steps {
                sh "podman build -t ${env.NEXUS_REGISTRY}/${IMAGE}:${params.VERSION} ."
            }
        }

        stage('Push to Nexus') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'nexus-credentials',
                                                   usernameVariable: 'NEXUS_USER',
                                                   passwordVariable: 'NEXUS_PASS')]) {
                    sh """
                        podman login --tls-verify=false ${env.NEXUS_REGISTRY} -u \$NEXUS_USER -p \$NEXUS_PASS
                        podman push ${env.NEXUS_REGISTRY}/${IMAGE}:${params.VERSION}
                    """
                }
            }
        }

    }

    post {
        success {
            echo "homedashboard-be ${params.VERSION} pushed to Nexus successfully"
        }
        failure {
            echo "Build/push of ${params.VERSION} failed"
        }
    }
}