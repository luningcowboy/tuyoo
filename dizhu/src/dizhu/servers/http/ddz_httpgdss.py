# -*- coding=utf-8
"""
Created on 2017年8月8日

@author: wangjifa
"""
import json

from dizhu.entity import dizhu_score_ranking, dizhu_util
from dizhu.entity.erdayi import PlayerData
from freetime.entity.msg import MsgPack
from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from hall.servers.util.rpc import user_remote
from poker.entity.biz.content import TYContentItem
from poker.entity.dao import userdata
from poker.protocol import runhttp
from poker.protocol.decorator import markHttpHandler, markHttpMethod
import freetime.util.log as ftlog
from poker.util import strutil


@markHttpHandler
class HttpGameHandler(BaseHttpMsgChecker):

    def makeResponse(self, result):
        return {'result':result}

    def _check_param_issueNum(self, key, params):
        value = runhttp.getParamStr(key)
        if value < 0:
            return 'param issueNum error', None
        return None, value

    def _check_param_rewardList(self, key, params):
        value = runhttp.getParamStr(key)
        if ftlog.is_debug():
            ftlog.debug('_check_param_rewardList key=', key, 'value=', value)
        try:
            value = json.loads(value)
        except:
            return 'param rewardList error', None
        return None, value

    def _check_param_score(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value < 0:
            return 'param score error', None
        return None, value

    def _check_param_rankId(self, key, params):
        rankId = runhttp.getParamStr(key)
        try:
            if not rankId:
                return None, None
            return None, rankId
        except:
            return 'param rankId error', rankId

    def _check_param_count(self, key, params):
        count = runhttp.getParamInt(key, 0)
        if not isinstance(count, int) or count == 0:
            return 'param count error, must be int and > 0', None
        return None, count

    def _check_param_days(self, key, params):
        days = runhttp.getParamInt(key, 0)
        if not isinstance(days, int) or days == 0:
            return 'param days error, must be int and > 0', None
        return None, days

    def checkCode(self):
        code = ''
        datas = runhttp.getDict()
        if 'code' in datas:
            code = datas['code']
            del datas['code']
        keys = sorted(datas.keys())
        checkstr = ''
        for k in keys:
            checkstr += k + '=' + datas[k] + '&'
        checkstr = checkstr[:-1]

        apikey = 'www.tuyoo.com-api-6dfa879490a249be9fbc92e97e4d898d-www.tuyoo.com'
        checkstr = checkstr + apikey
        if code != strutil.md5digest(checkstr):
            return -1, 'Verify code error'

        # acttime = int(datas.get('time', 0))
        # if abs(time.time() - acttime) > 10:
        #     return -1, 'verify time error'
        return 0, None


    @markHttpMethod(httppath='/_gdss/user/init_user_data_gdss')
    def doExecuteCmd(self, userId, rankId, issueNum):
        """
        :param userId: 玩家userId
        :param rankId: 排行榜类型 '0' 万元争霸赛 '1' 千元擂台赛
        :param issueNum: 排行榜期号 格式：20170807
        :return: 返回处理结果信息 
        """
        ret = 0
        if len(str(issueNum)) != 8:
            return self.makeResponse({'score_execute_cmd issueNum Error. rankId': rankId, 'issueNum=': issueNum})
        issueNum = str(issueNum)
        userData = dizhu_score_ranking.loadUserData(userId, rankId, issueNum)
        if userData:
            ftlog.info('init_user_data_gdss del scoreRanking userData=', userData.toDict())

            userData = dizhu_score_ranking.UserData(userId, rankId, issueNum)
            ret = dizhu_score_ranking.saveUserData(userData)
            rankingDefine = dizhu_score_ranking.getConf().findRankingDefine(rankId)
            rankLimit = rankingDefine.rankLimit if rankingDefine else 3000
            dizhu_score_ranking.insertRanklist(rankId, issueNum, userData.userId, userData.score, rankLimit)

            ftlog.info('init_user_data_gdss del scoreRanking userData success. userData=', userData.toDict())
        else:
            ftlog.info('init_user_data_gdss no userData in rankingList userId=', userId,
                       'rankId=', rankId, 'issueNum=', issueNum)
            return self.makeResponse({'init_user_data_gdss no userData in rankingList userId=': userId,
                                      'rankId': rankId, 'issueNum=': issueNum})

        return self.makeResponse({'init_user_data_gdss del scoreRanking userData success. userData=': userData.toDict(), 'execute over ret=': ret})

    @markHttpMethod(httppath='/_gdss/user/del_user_score_gdss')
    def doDelUserScore(self, userId, rankId, issueNum, score):
        """
        :param userId: 玩家userId
        :param rankId: 排行榜类型 '0' 万元争霸赛 '1' 千元擂台赛
        :param issueNum: 排行榜期号 格式：20170807
        :param score: 扣除的积分数量
        :return: 返回处理结果信息 
        """
        ret = 0
        if len(issueNum) != 8:
            return self.makeResponse({'del_user_score_gdss issueNum Error. rankId': rankId, 'issueNum=': issueNum})

        issueNum = str(issueNum)

        userData = dizhu_score_ranking.loadUserData(userId, rankId, issueNum)
        if userData:
            ftlog.info('del_user_score_gdss del scoreRanking userData=', userData.toDict())

            score = max(0, score)
            userData.score -= score
            userData.score = max(0, userData.score)

            ret = dizhu_score_ranking.saveUserData(userData)
            rankingDefine = dizhu_score_ranking.getConf().findRankingDefine(rankId)
            rankLimit = rankingDefine.rankLimit if rankingDefine else 3000
            dizhu_score_ranking.insertRanklist(rankId, issueNum, userData.userId, userData.score, rankLimit)

            ftlog.info('del_user_score_gdss del scoreRanking userData success. userData=', userData.toDict())
        else:
            ftlog.info('del_user_score_gdss no userData in rankingList userId=', userId, 'rankId=', rankId, 'issueNum=',
                       issueNum)
            return self.makeResponse(
                {'init_user_data_gdss no userData in rankingList userId=': userId, 'rankId': rankId,
                 'issueNum=': issueNum})

        return self.makeResponse({'del_user_score_gdss del scoreRanking userData success. userData=': userData.toDict(),
                                  'execute over ret=': ret})


    @markHttpMethod(httppath='/_gdss/user/get_rank_list')
    def doGetRankList(self, rankId, issueNum):
        """
        :param rankId: 
        :param issueNum: 
        :return: 获取issueNum对应期号的排行榜userId 
        """
        if len(issueNum) != 8:
            return self.makeResponse({'get_rank_list issueNum Error. rankId': rankId, 'issueNum=': issueNum})

        rankList = dizhu_score_ranking.getRanklist(rankId, issueNum, 0, -1)
        ftlog.info('get_rank_list del scoreRanking userData success. userData=', rankList)

        rankingInfo = dizhu_score_ranking.loadRankingInfo(rankId)
        d = rankingInfo.toDict()

        return self.makeResponse({'rankId': rankId, 'info': d, 'rankList': rankList})


    @markHttpMethod(httppath='/_gdss/user/change_erdayi_bind_mobile')
    def changeErdayiBindMobile(self, userId, oldMobile, newMobile):
        """
        竞技二打一修改玩家绑定手机接口
        :param userId: 
        :param oldMobile: 原绑定手机号
        :param newMobile: 新绑定手机号
        :return: 
        """
        realinfo = PlayerData.getRealInfo(userId)
        if realinfo and realinfo.get('idNo'):
            mobile = realinfo.get('mobile')
            realName = realinfo.get('realname')

            if mobile and mobile == oldMobile:
                realinfo['mobile'] = newMobile
                PlayerData.setRealInfo(userId, realinfo)
                ftlog.info('erdayiChangeUserBindMobile success. userId=', userId,
                           'realName=', realName,
                           'realInfo=', realinfo)
            else:
                ftlog.info('changeErdayiBindMobile failed. userId=', userId, 'realInfo=', realinfo)

        ftlog.info('changeErdayiBindMobile userId=', userId, 'realInfo=', realinfo)

    @markHttpMethod(httppath='/_gdss/user/change_user_wx_diamond')
    def chargeUserWxDiamond(self, userId, count):
        """
        给微信用户补充钻石接口
        """
        mo = MsgPack()
        ec, result = self.checkCode()
        if ec == 0:
            if count >= 10001 or count < -10001:
                ec = 1
                result = 'diamond count to much !!'
            else:
                if userdata.checkUserData(userId):
                    contentItems = [{'itemId': 'item:1311', 'count': abs(count)}]
                    if count > 0:
                        success = user_remote.addAssets(6, userId, contentItems, 'CHARGE_USER_WX_DIAMOND', 0)
                        ftlog.info('chargeUserWxDiamond userId=', userId, 'count=', count, 'success=', success)
                        mo.setResult('success', 1)
                        mo.setResult('count', count)
                    else:
                        assetKindId, retCount = user_remote.consumeAssets(6, userId, contentItems, 'CHARGE_USER_WX_DIAMOND', 0)
                        if not assetKindId:
                            mo.setResult('success', 1)
                            mo.setResult('count', count)
                            ftlog.info('consumeUserWxDiamond userId=', userId, 'count=', count, 'assetKindId=', assetKindId, 'retCount=', retCount)
                        else:
                            ec = 3
                            result = 'user diamond < %s' % abs(count)
                else:
                    ec, result = 2, 'userId error !!'
        if ec != 0:
            mo.setError(ec, result)
        return mo

    @markHttpMethod(httppath='/_gdss/user/signed/reward')
    def doGdssUserSignedReward(self, userId, rewardList, days):
        ''' 公众号签到奖励 '''
        mo = MsgPack()
        ec, result = self.checkCode()
        if ec == 0:
            if userdata.checkUserData(userId):
                if rewardList:
                    try:
                        contentItems = TYContentItem.decodeList(rewardList)
                        mailstr = "签到奖励#恭喜您获得连续签到%s天：${rewardContent}奖励！记得每天去签到哟~" % days
                        assetList = dizhu_util.sendRewardItems(userId, contentItems, mailstr, 'DIZHU_GDSS_SIGNED_REWARD', 0)
                        from dizhu.game import TGDizhu
                        from dizhu.entity.common.events import ActiveEvent
                        TGDizhu.getEventBus().publishEvent(ActiveEvent(6, userId, 'signIn'))
                        if ftlog.is_debug():
                            ftlog.debug('doGdssUserSignedReward userId=', userId, 'rewardList=', rewardList)
                    except:
                        ec, result = 1, 'reward error !!'
                else:
                    ec, result = 1, 'reward error !!'
            else:
                ec, result = 2, 'userId error !!'
        if ec != 0:
            mo.setError(ec, result)
        return mo
