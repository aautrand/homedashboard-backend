pipeline {
    agent any

    parameters {
        string(name: 'VERSION', description: 'New version to release (e.g. 1.4.2)', trim: true)
    }

    environment {
        NEXUS_REGISTRY = 'localhost:8082'
        IMAGE          = 'homedashboard-be'
        CONTAINER_FILE = '/home/aautrand/.config/containers/systemd/homedashboard-be.container'
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

        stage('Bump Version') {
            steps {
                sh "echo '${params.VERSION}' > version"
                sh '''
                    git config user.email "jenkins@local"
                    git config user.name "Jenkins"
                    git add version
                    git commit -m "[system] Bump version to ${VERSION}"
                '''
                withCredentials([usernamePassword(credentialsId: 'forgejo-token',
                                                   usernameVariable: 'GIT_USER',
                                                   passwordVariable: 'GIT_TOKEN')]) {
                    sh 'git push http://${GIT_USER}:${GIT_TOKEN}@git.example.internal/aautrand/homedashboard-be.git HEAD:dev'
                }
            }
        }

        stage('Build') {
            steps {
                sh "podman build -t ${NEXUS_REGISTRY}/${IMAGE}:${params.VERSION} ."
            }
        }

        stage('Push to Nexus') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'nexus-credentials',
                                                   usernameVariable: 'NEXUS_USER',
                                                   passwordVariable: 'NEXUS_PASS')]) {
                    sh """
                        podman login --tls-verify=false ${NEXUS_REGISTRY} -u \$NEXUS_USER -p \$NEXUS_PASS
                        podman push ${NEXUS_REGISTRY}/${IMAGE}:${params.VERSION}
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                sshagent(['aautrand-deploy-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no aautrand@localhost '
                            sed -i "s|^Image=.*|Image=${NEXUS_REGISTRY}/${IMAGE}:${params.VERSION}|" ${CONTAINER_FILE}
                            XDG_RUNTIME_DIR=/run/user/\$(id -u) systemctl --user daemon-reload
                            XDG_RUNTIME_DIR=/run/user/\$(id -u) systemctl --user restart homedashboard-be
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "homedashboard-be ${params.VERSION} deployed successfully"
        }
        failure {
            echo "Deployment of ${params.VERSION} failed"
        }
    }
}