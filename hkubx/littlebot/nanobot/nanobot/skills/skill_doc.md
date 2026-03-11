● ClawHub 是一个公共的 skill 注册中心，通过 npx 命令来搜索和安装 skills。                                                                                                                                     
                                                                  
  使用方式                                                                                                                                                                                                    
                                                                                                                                                                                                              
  1. 搜索 skills                                                                                                                                                                                              
                                                                                                                                                                                                              
  npx --yes clawhub@latest search "web scraping" --limit 5        

  2. 安装 skill

  npx --yes clawhub@latest install <slug> --workdir ~/.nanobot/workspace

  3. 更新已安装的 skills

  npx --yes clawhub@latest update --all --workdir ~/.nanobot/workspace

  4. 列出已安装的 skills

  npx --yes clawhub@latest list --workdir ~/.nanobot/workspace