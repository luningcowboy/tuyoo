# -*- coding=utf-8
'''
Created on 2015年6月24日

@author: zhaojiangang
'''

import base64
from datetime import datetime
import json
from sre_compile import isstring
import time

from hall.servers.util.user_coupon_detail_handler import UserCouponDetailsTcpHandler
from freetime.entity.msg import MsgPack
import freetime.util.log as ftlog
from hall.entity import hallaccount, hallitem, hallstore, datachangenotify, \
    hallgamelist2, halldailycheckin, hallads, hallranking, hallexchange, \
    hallbenefits, hallsubmember, fivestarrate, hall_first_recharge, hallled, \
    halldomains, hall_game_update, hallroulette, hallpopwnd, hall_friend_table, \
    hall_fangka, hall_wxappid, hall_fangka_buy_info, hall_exmall, hall_share2, \
    hall_yyb_gifts, hall_red_packet_task
from hall.entity.hall_share2 import ParsedClientId
from hall.entity.hallactivity.activity_exchange_code import \
    TYActivityExchangeCode
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.hallitem import TYItemNotEnoughException, TYDecroationItemKind, \
    TYDecroationItem
from hall.entity.hallusercond import UserConditionRegister
from hall.entity.todotask import TodoTaskHelper, TodoTaskAddExitNotification, \
    TodoTaskDownloadOrOpenThirdApp, TodoTaskVipLevelUp, TodoTaskTriggerEvent, \
    TodoTaskThirdSDKExtend
from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from hall.servers.http.httpgame import HttpGameHandler
from hall.servers.util import exmall_handler
from hall.servers.util.account_handler import AccountTcpHandler
from hall.servers.util.ads_handler import AdsHelper
from hall.servers.util.decroation_handler import DecroationHelper
from hall.servers.util.hall_handler import HallHelper
from hall.servers.util.hall_invite_handler import InviteTcpHandler
from hall.servers.util.item_handler import ItemHelper
from hall.servers.util.red_packet_task_handler import RedPacketTaskTcpHandler
from hall.servers.util.rpc import user_remote, hall_exmall_remote, \
    hall_yyb_gifts_remote, hall_invite_remote, vip_remote, exchange_remote
from hall.servers.util.share2_handler import Share2TcpHandler
from hall.servers.util.store_handler import StoreHelper
from hall.servers.util.vip_handler import VipTcpHandler
from poker.entity.biz.exceptions import TYBizException
from poker.entity.configure import gdata, configure
from poker.entity.dao import gamedata as pkgamedata, sessiondata, daobase, \
    userchip, gamedata, userdata
from poker.protocol import runhttp, router
from poker.protocol.decorator import markHttpHandler, markHttpMethod
from poker.util import strutil
import poker.util.timestamp as pktimestamp
from hall.servers.util.red_packet_exchange_handler import RedPacketExchangeTcpHandler
from hall.servers.util.red_packet_main_handler import RedPacketMainTcpHandler


@markHttpHandler
class TestHttpHandler(BaseHttpMsgChecker):

    def __init__(self):
        pass
    
    
    def isEnable(self):
        return gdata.enableTestHtml()
    
    def makeErrorResponse(self, ec, message):
        return {'error':{'ec':ec, 'message':message}}
    
    def makeResponse(self, result):
        return {'result':result}
    
    def _check_param_exchangeCount(self, key, params):
        value = runhttp.getParamInt(key, 0)
        return None, value
    
    def _check_param_exchangeParams(self, key, params):
        value = runhttp.getParamStr(key)
        if value:
            value = strutil.loads(value)
        else:
            value = {}
        return None, value
    
    def _check_param_vipExp(self, key, params):
        vipExp = runhttp.getParamInt(key, 0)
        return None, vipExp
    
    def _check_param_level(self, key, params):
        level = runhttp.getParamInt(key, 0)
        return None, level
    
    def _check_param_count(self, key, params):
        count = runhttp.getParamInt(key, 0)
        return None, count
    
    def _check_param_score(self, key, params):
        value = runhttp.getParamInt(key, 0)
        return None, value
    
    def _check_param_rankingId(self, key, params):
        rankingId = runhttp.getParamInt(key, 0)
        return None, rankingId
    
    def _check_param_userIds(self, key, params):
        try:
            jstr = runhttp.getParamStr(key)
            userIdList = jstr.split(',')
            ret = []
            for userId in userIdList:
                ret.append(int(userId))
            return None, ret
        except:
            return 'the jsonstr params is not a list Format !!', None
        
    def _check_param_rankKey(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return self.makeErrorResponse(-1, '必须指定rankKey'), None
        return None, value
    
    def _check_param_inputType(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return self.makeErrorResponse(-1, '必须指定inputType'), None
        return None, value
    
    def _check_param_action(self, key, params):
        action = runhttp.getParamStr(key, '')
        if not action:
            return self.makeErrorResponse(-1, '必须指定要执行哪个动作'), None
        return None, action
    
    def _check_param_newName(self, key, params):
        newName = runhttp.getParamStr(key, '')
        if not newName or not isstring(newName):
            return self.makeErrorResponse(-1, '必须指定新昵称'), None
        return None, newName
    
    def _check_param_kindId(self, key, params):
        kindId = runhttp.getParamInt(key, 0)
        if kindId <= 0:
            return self.makeErrorResponse(-1, '没有指定道具类型'), None
        return None, kindId
    
    def _check_param_exchangeId(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定exchangeId'), None
        return None, value
    
    def _check_param_result(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value < 0:
            return self.makeErrorResponse(-1, '没有指定审核结果'), None
        return None, value
    
    def _check_param_times(self, key, params):
        times = runhttp.getParamInt(key, -1)
        if times < 0:
            return self.makeErrorResponse(-1, 'times必须是>=0的整数'), None
        return None, times
    
    def _check_param_today(self, key, params):
        today = runhttp.getParamStr(key, '')
        if today:
            today = datetime.strptime(today, '%Y%m%d').date()
        else:
            today = datetime.now().date()
        return None, today
    
    def _check_param_itemId(self, key, params):
        itemId = runhttp.getParamInt(key, 0)
        if itemId <= 0:
            return self.makeErrorResponse(-1, '道具ID必须是>0的整数'), None
        return None, itemId
    
    def _check_param_expires(self, key, params):
        expires = runhttp.getParamStr(key)
        if not expires or not isstring(expires):
            return self.makeErrorResponse(-1, '必须指定到期时间'), None
        return None, expires
    
    def _check_param_createTime(self, key, params):
        createTime = runhttp.getParamStr(key)
        if not createTime or not isstring(createTime):
            return self.makeErrorResponse(-1, '必须指定创建时间'), None
        return None, createTime
    
    def _check_param_productId(self, key, params):
        productId = runhttp.getParamStr(key)
        if not productId or not isstring(productId):
            return self.makeErrorResponse(-1, '必须指定要购买的商品'), None
        return None, productId
    
    def _check_param_prodId(self, key, params):
        productId = runhttp.getParamStr(key)
        if not productId or not isstring(productId):
            return self.makeErrorResponse(-1, '必须指定商品ID'), None
        return None, productId
    
    def _check_param_orderId(self, key, params):
        orderId = runhttp.getParamStr(key)
        if not orderId or not isstring(orderId):
            return self.makeErrorResponse(-1, '必须指定orderId'), None
        return None, orderId
    
    def _check_param_promoteCode(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定promoteCode'), None
        return None, value
    
    def _check_param_taskId(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定taskId'), None
        return None, value
    
    def _check_param_time(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定召回提醒时间'), None
        return None, value
    
    def _check_param_dsc(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定召回提醒内容'), None
        return None, value
    
    # packageName
    def _check_param_packageName(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定包名/Bundle ID'), None
        return None, value
    
    # scheme
    def _check_param_scheme(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定scheme'), None
        return None, value
    
    # appCode
    def _check_param_appCode(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的appCode'), None
        return None, value
    
    # downloadUrl
    def _check_param_downloadUrl(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的downloadUrl'), None
        return None, value
    
    # downloadType
    def _check_param_downloadType(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的downloadType'), None
        return None, value
    
    # MD5
    def _check_param_MD5(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的MD5'), None
        return None, value
    
    # event
    def _check_param_event(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的event'), None
        return None, value

    # led
    def _check_param_led(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的led'), None
        return None, value

    # scope
    def _check_param_scope(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的scope'), None
        return None, value
    
    # shareId
    def _check_param_shareId(self, key, params):
        shareId = runhttp.getParamStr(key, '')
        if not shareId:
            return self.makeErrorResponse(-1, '必须指定要检查哪个分享ID'), None
        return None, shareId
    
    # version
    def _check_param_version(self, key, params):
        version = runhttp.getParamStr(key, '')
        if not version:
            return self.makeErrorResponse(-1, '必须指定要游戏版本'), None
        return None, version
    
    # updateVersion
    def _check_param_updateVersion(self, key, params):
        updateVersion = runhttp.getParamStr(key, '')
        if not updateVersion:
            return self.makeErrorResponse(-1, '必须指定要游戏更新版本'), None
        return None, updateVersion

    def _check_param_activityId(self, key, params):
        actid = runhttp.getParamStr(key)
        if not actid:
            return self.makeErrorResponse(-1, '必须指定要活动id'), None
        return None, actid
    
    def _check_param_urlParams(self, key, params):
        value = runhttp.getParamStr(key)
        if not value:
            return None, {}
        try:
            value = strutil.loads(value)
        except:
            return 'urlParams必须是json字符串', None
        return None, value

    def _check_param_whereToShare(self, key, params):
        whereToShare = runhttp.getParamStr(key)
        if not whereToShare:
            return self.makeErrorResponse(-1, 'ERROR of whereToShare !'), None
        return None, whereToShare
    
    @markHttpMethod(httppath='/gtest/user/rename/check')
    def doRenameCheck(self, userId):
        ftlog.info('TestHttpHandler.doRenameCheck userId=', userId)
        mo = AccountTcpHandler._doChangeNameCheck(userId, sessiondata.getClientId(userId))
        return self.makeResponse(mo.pack())
    
    @markHttpMethod(httppath='/gtest/user/rename/try')
    def doRenameTry(self, userId, newName):
        ftlog.info('TestHttpHandler.doRenameTry userId=', userId)
        mo = AccountTcpHandler._doChangeNameTry(userId, sessiondata.getClientId(userId), newName)
        return self.makeResponse(mo.pack())
    
    @markHttpMethod(httppath='/gtest/game/list')
    def doHttpGameList(self):
        ftlog.info('TestHttpHandler.doHttpGameList')
        gameIdList = list(gdata.gameIds())
        gameIdList.sort()
        return self.makeResponse(gameIdList)
    
    @markHttpMethod(httppath='/gtest/item/list')
    def doHttpItemList(self):
        ftlog.info('TestHttpHandler.doHttpItemList')
        itemKindList = hallitem.itemSystem.getAllItemKind()
        ret = []
        for itemKind in itemKindList:
            ret.append({
                'kindId':itemKind.kindId,
                'displayName':itemKind.displayName,
                'masks':itemKind.masks if isinstance(itemKind, TYDecroationItemKind) else 0
            })
        return self.makeResponse(ret)
    
    def _encodeItem(self, userBag, item, timestamp):
        return {
            'itemId':item.itemId,
            'kindId':item.kindId,
            'displayName':item.itemKind.displayName,
            'pic':item.itemKind.pic,
            'count':item.balance(timestamp),
            'units':item.itemKind.units.displayName,
            'actions':ItemHelper.encodeItemActionList(9999, userBag, item, timestamp)
        }
        
    @markHttpMethod(httppath='/gtest/user/vip/setExp')
    def doVipSetExp(self, userId, vipExp):
        ftlog.info('TestHttpHandler.doVipSetExp userId=', userId,
                   'vipExp=', vipExp)
        
        pkgamedata.setGameAttr(userId, 9999, 'vip.exp', vipExp)
        return self.makeResponse({'userId':userId, 'vipExp':vipExp})
    
    @markHttpMethod(httppath='/gtest/user/vip/addExp')
    def doVipAddExp(self, userId, vipExp):
        ftlog.info('TestHttpHandler.doVipAddExp userId=', userId,
                   'vipExp=', vipExp)
        
        mo = vip_remote.addVipExp(9999, userId, vipExp)
        return self.makeResponse({'userId':userId, 'msg':mo})
    
    @markHttpMethod(httppath='/gtest/user/vip/vipInfo')
    def doVipInfo(self, userId):
        ftlog.info('TestHttpHandler.doVipAddExp userId=', userId)
        
        mo = VipTcpHandler._doNewVipInfo(9999, userId)
        return self.makeResponse({'userId':userId, 'msg':mo._ht})
    
    @markHttpMethod(httppath='/gtest/user/vip/vipGift')
    def doVipGift(self, userId, level):
        ftlog.info('TestHttpHandler.doVipGift userId=', userId,
                   'level=', level)
        mo = VipTcpHandler._doNewVipGift(9999, userId, level)
        return self.makeResponse({'userId':userId, 'msg':mo._ht})
    
    @markHttpMethod(httppath='/gtest/user/vip/setGiftState')
    def doSetVipGiftState(self, userId, level):
        ftlog.info('TestHttpHandler.doVipGift userId=', userId,
                   'level=', level)
        
        pkgamedata.delGameAttr(userId, 9999, 'vip.gift.states')
        
        msg = MsgPack()
        msg.setCmd('newvip')
        msg.setParam('action', 'vipInfo')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        mo = router.queryUtilServer(msg, userId)
        return self.makeResponse({'userId':userId, 'msg':mo._ht})
    
    @markHttpMethod(httppath='/gtest/user/item/list')
    def doHttpUserItemList(self, userId):
        ftlog.info('TestHttpHandler.doHttpUserItemList')
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        userItemList = []
        timestamp = pktimestamp.getCurrentTimestamp()
        for item in userBag.getAllItem():
            userItemList.append(self._encodeItem(userBag, item, timestamp))
        return self.makeResponse({'userId':userId, 'items':userItemList})
    
    @markHttpMethod(httppath='/gtest/user/item/incr')
    def doHttpUserItemIncr(self, gameId, userId, kindId, count):
        ftlog.info('TestHttpHandler.doHttpUserItemIncr gameId=', gameId,
                   'userId=', userId,
                   'kindId=', kindId,
                   'count=', count)
        if count > 0:
            return self._doHttpUserItemAdd(gameId, userId, kindId, count)
        elif count < 0:
            return self._doHttpUserItemConsume(gameId, userId, kindId, -count)
        return self.makeErrorResponse(-1, '数量不能为0')
    
    @markHttpMethod(httppath='/gtest/user/item/remove')
    def doHttpUserItemRemove(self, gameId, userId, itemId):
        ftlog.info('TestHttpHandler.doHttpUserItemRemove gameId=', gameId,
                   'userId=', userId,
                   'itemId=', itemId)
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        if not item:
            return self.makeErrorResponse(-1, '没有这个道具')
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag.removeItem(gameId, item, timestamp, 'test', 0)
        userItemList = []
        for item in userBag.getAllItem():
            userItemList.append(self._encodeItem(userBag, item, timestamp))
        return self.makeResponse({'userId':userId, 'items':userItemList})
    
    @markHttpMethod(httppath='/gtest/user/item/setExpires')
    def doHttpUserItemExpires(self, userId, itemId, expires):
        ftlog.info('TestHttpHandler.doHttpUserItemExpires userId=', userId,
                   'itemId=', itemId,
                   'expires=', expires)
        expiresTimestamp = time.mktime(datetime.strptime(expires, '%Y-%m-%d %H:%M:%S').timetuple())
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        timestamp = int(time.time())
        if not item:
            return self.makeErrorResponse(-1, '没有这个道具')
        if item.itemKind.units.isTiming():
            item.expiresTime = expiresTimestamp
            userBag.updateItem(6, item, timestamp)
            datachangenotify.sendDataChangeNotify(6, userId, 'item')
            return self.makeResponse({'userId':userId, 'item':self._encodeItem(userBag, item, timestamp)})
        return self.makeErrorResponse(-1, '该道具不是时间类型的')
    
    @markHttpMethod(httppath='/gtest/user/item/setCreateTime')
    def doHttpUserItemCreateTime(self, userId, itemId, createTime):
        ftlog.info('TestHttpHandler.doHttpUserItemCreateTime userId=', userId,
                   'itemId=', itemId,
                   'createTime=', createTime)
        createTimeTimestamp = time.mktime(datetime.strptime(createTime, '%Y-%m-%d %H:%M:%S').timetuple())
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        timestamp = int(time.time())
        if not item:
            return self.makeErrorResponse(-1, '没有这个道具')
        item.createTime = createTimeTimestamp
        userBag.updateItem(6, item, timestamp)
        datachangenotify.sendDataChangeNotify(6, userId, 'item')
        return self.makeResponse({'userId':userId, 'item':self._encodeItem(userBag, item, timestamp)})
    
    def _doHttpUserItemAdd(self, gameId, userId, kindId, count):
        ftlog.info('TestHttpHandler.doHttpUserItemAdd')
        itemKind = hallitem.itemSystem.findItemKind(kindId)
        if not itemKind:
            return self.makeErrorResponse(-1, '不能识别的道具类型')
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.addItemUnitsByKind(gameId, itemKind, count, timestamp, 0,
                                          'TEST_ADJUST', 0)[0]
        changed = ['item']
        if isinstance(item, TYDecroationItem):
            changed.append('decoration')
        datachangenotify.sendDataChangeNotify(gameId, userId, changed)
        return self.makeResponse({'userId':userId, 'item':self._encodeItem(userBag, item, timestamp)})
    
    def _doHttpUserItemConsume(self, gameId, userId, kindId, count):
        ftlog.info('TestHttpHandler.doHttpUserItemConsume')
        itemKind = hallitem.itemSystem.findItemKind(kindId)
        if not itemKind:
            return self.makeErrorResponse(-1, '不能识别的道具类型')
        if count <= 0:
            return self.makeErrorResponse(-1, '数量必须大于0')
        
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        try:
            consumeCount = userBag.consumeUnitsCountByKind(gameId, itemKind, count, timestamp,
                                                           'TEST_ADJUST', 0)
            changed = ['item']
            if isinstance(itemKind, TYDecroationItemKind):
                changed.append('decoration')
            datachangenotify.sendDataChangeNotify(gameId, userId, changed)
            return self.makeResponse({'userId':userId, 'consumeCount':consumeCount, 'kindId':kindId})
        except TYItemNotEnoughException:
            return self.makeErrorResponse(-1, '道具数量不足')

    def _buildParams(self, userBag, item, actionName):
        params = {}
        action = item.itemKind.findActionByName(actionName)
        if action:
            paramNameTypeList = action.getParamNameTypeList()
            if paramNameTypeList:
                for paramName, paramTypes in paramNameTypeList:
                    if isinstance(paramTypes, (list, tuple)):
                        value = paramTypes[0](runhttp.getParamStr(paramName, ''))
                    else:
                        value = paramTypes(runhttp.getParamStr(paramName, ''))
                    params[paramName] = value
        if actionName == 'exchange':
            if 'phone' not in params:
                params['phoneNumber'] = '18618378234'
        return params
        
    @markHttpMethod(httppath='/gtest/user/item/action')
    def doHttpUserItemAction(self, gameId, userId, itemId, action):
        ftlog.info('TestHttpHandler.doHttpUserItemAction')
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        if not item:
            return self.makeErrorResponse(-1, '没有找到该道具')
        try:
            params = self._buildParams(userBag, item, action)
            actionResult = userBag.doAction(gameId, item, action, timestamp, params)
            ftlog.info('doHttpUserItemAction gameId=', gameId,
                       'userId=', userId,
                       'itemId=', itemId,
                       'action=', action,
                       'params=', params,
                       'result=', actionResult)
            datachangenotify.sendDataChangeNotify(gameId, userId, 'item')
            return self.makeResponse({'userId':userId, 'item':self._encodeItem(userBag, item, timestamp)})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
    
    @markHttpMethod(httppath='/gtest/user/exchange/listRecord')
    def doHttpUserExchangeList(self, userId):
        records = hallexchange.getExchangeRecords(userId)
        ret = []
        for record in records:
            if record.itemKindId:
                itemKind = hallitem.itemSystem.findItemKind(record.itemKindId)
                if itemKind:
                    ret.append({
                        'exchangeId':record.exchangeId,
                        'date':datetime.fromtimestamp(record.createTime).strftime('%Y-%m-%d'),
                        'consume':itemKind.displayName,
                        'consumeCount':1,
                        'gotItem':record.params.get('desc'),
                        'state':record.state
                    })
            else:
                amount = float(record.params.get('count', 0)) / 10
                displayName = '%.2f现金' % (amount)
                ret.append({
                    'exchangeId':record.exchangeId,
                    'wxappId':record.params.get('wxappId'),
                    'date':datetime.fromtimestamp(record.createTime).strftime('%Y-%m-%d'),
                    'consume':displayName,
                    'consumeCount':record.params.get('count'),
                    'gotItem':record.params.get('desc'),
                    'state':record.state
                })
        return self.makeResponse(ret)
    
    @markHttpMethod(httppath='/gtest/user/exchange/audit')
    def doHttpUserExchangeAudit(self, userId, exchangeId, result):
        ec, info = exchange_remote.handleAuditResult(HALL_GAMEID, userId, exchangeId, result)
        return {'ec':ec, 'info':info}
    
    @markHttpMethod(httppath='/gtest/user/exchange/shipping')
    def doHttpUserExchangeShipping(self, userId, exchangeId, result):
        ec, info = exchange_remote.handleShippingResult(HALL_GAMEID, userId, exchangeId, result)
        return {'ec':ec, 'info':info}
    
    @markHttpMethod(httppath='/gtest/rank/setUser')
    def doHttpRankSetUser(self, gameId, userId, inputType, score):
        ranks = {}
        timestamp = pktimestamp.getCurrentTimestamp()
        rankingUserMap = hallranking.rankingSystem.setUserByInputType(gameId, inputType, userId, score, timestamp)
        for rankingId, rankingUser in rankingUserMap.iteritems():
            ranks[rankingId] = {
                'score':rankingUser.score,
                'rank':rankingUser.rank,
                'userId':rankingUser.userId
            }
        return self.makeResponse(ranks)
    
    @markHttpMethod(httppath='/gtest/rank/removeUser')
    def doHttpRankRemoveUser(self, gameId, userId, inputType):
        timestamp = pktimestamp.getCurrentTimestamp()
        hallranking.rankingSystem.removeUserByInputType(gameId, inputType, userId, timestamp)
        return self.makeResponse({'userId':userId, 'inputType':inputType})
    
    @markHttpMethod(httppath='/gtest/rank/getRank')
    def doHttpRankQuery(self, gameId, userId, rankKey, clientId):
        msg = MsgPack()
        msg.setCmd('custom_rank')
        msg.setParam('action', 'query')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        msg.setParam('rankKey', rankKey)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/rank/remove')
    def doRemoveRank(self, rankingId):
        try:
            hallranking.rankingSystem.removeRanking(rankingId)
            return self.makeResponse({'rankingId':rankingId})
        except:
            ftlog.exception()
            return self.makeErrorResponse(1, 'exception')
    
    @markHttpMethod(httppath='/gtest/rank/removeAll')
    def doRemoveAllRank(self, rankingId):
        try:
            rankingDefineList = hallranking.rankingSystem.getRankingDefines()
            for rankingDefine in rankingDefineList:
                hallranking.rankingSystem.removeRanking(rankingDefine.rankingId)
            return self.makeResponse({})
        except:
            ftlog.exception()
            return self.makeErrorResponse(1, 'exception')
        
    @markHttpMethod(httppath='/gtest/rank/removeAllStatus')
    def doRemoveAllRankStatus(self):
        try:
            rankingDefineList = hallranking.rankingSystem.getRankingDefines()
            for rankingDefine in rankingDefineList:
                daobase.executeMixCmd('del', 'ranking.status:%s' % (rankingDefine.rankingId))
            return self.makeResponse({})
        except:
            ftlog.exception()
            return self.makeErrorResponse(1, 'exception')
    
    @markHttpMethod(httppath='/gtest/ads/queryResponse')
    def doHttpQueryAdsResponse(self, gameId, userId, clientId):
        adsTemplate = hallads.queryAds(gameId, userId, clientId)
        mo = AdsHelper.makeAdsQueryResponse(gameId, userId, clientId, adsTemplate)
        return self.makeResponse(mo._ht)

    @markHttpMethod(httppath='/gtest/ads/queryConfig')
    def doHttpQueryAdsConfig(self, gameId, userId, clientId):
        import pickle
        adsTemplate = hallads.queryAds(gameId, userId, clientId)
        return pickle.dumps(adsTemplate)

    @markHttpMethod(httppath='/gtest/user/decroation/query')
    def doDecroationQuery(self, userIds):
        ftlog.info('TestHttpHandler.doDecroationQuery userIds=', userIds)
        mo = DecroationHelper.makeDecroationQueryResponse(HALL_GAMEID, userIds, 0)
        return self.makeResponse(mo._ht)
    
    @markHttpMethod(httppath='/gtest/user/decroation/config')
    def doDecroationConfig(self, userId):
        ftlog.info('TestHttpHandler.doDecroationConfig userId=', userId)
        mo = DecroationHelper.makeDecoroationConfigResponse(HALL_GAMEID, userId)
        return self.makeResponse(mo._ht)
    
    def _encodeShelves(self, shelves):
        return {
            'name':shelves.name,
            'displayName':shelves.displayName,
            'isVisible':shelves.visibleInStore,
            'iconType':shelves.iconType,
            'sortValue':shelves.sortValue,
            'products':[StoreHelper.buildProductInfo(product) for product in shelves.productList]
        }

    @markHttpMethod(httppath='/gtest/store/shelves/list')
    def doHttpShelvesList(self, gameId, userId, clientId):
        try:
            if not clientId:
                clientId = sessiondata.getClientId(userId)
            ret = []
            shelvesList = hallstore.storeSystem.getShelvesListByClientId(gameId, userId, clientId)
            ftlog.debug('TestHttpHandler.doHttpShelvesList gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'shelvesList=', shelvesList)
            if shelvesList:
                shelvesList.sort(key=lambda shelves:shelves.sortValue)
                for shelves in shelvesList:
                    if shelves.visibleInStore:
                        ret.append(self._encodeShelves(shelves))
            return self.makeResponse({'userId':userId, 'shelvesList':ret})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/store/buy')
    def doHttpBuyProduct(self, gameId, userId, clientId, productId, orderId, count):
        try:
            product = hallstore.storeSystem.findProduct(productId)
            if product.buyType == 'exchange':
                msg = MsgPack()
                msg.setCmd('store')
                msg.setParam('action', 'buy')
                msg.setParam('gameId', gameId)
                msg.setParam('prodId', productId)
                msg.setParam('userId', userId)
                msg.setParam('clientId', clientId)
                router.sendUtilServer(msg, userId)
                return self.makeResponse({'userId':userId, 'productId':productId})
#                 orderDeliveryResult = hallstore.exchangeProduct(gameId, userId, clientId,
#                                                                 orderId, productId, count)
#                 mo = StoreHelper.makeProductDeliveryResponse(userId, orderDeliveryResult)
#                 return mo.pack()
            else:
                order = hallstore.storeSystem.buyProduct(gameId, gameId, userId, clientId, orderId, productId, count)
                return self.makeResponse({'userId':userId, 'productId':productId, 'orderId':order.orderId})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
    
    @markHttpMethod(httppath='/gtest/dizhu/store/deliveryOrder')
    def doHttpDeliveryOrder(self, gameId, userId, clientId, prodId, orderId, count):
        try:
            product = hallstore.storeSystem.findProduct(prodId)
            if product.buyType == 'exchange':
                return self.makeErrorResponse(-1, '兑换类商品不能发货')
            isSub = runhttp.getParamInt('isSub', 0)
            
            msg = MsgPack()
            msg.setCmd('prod_delivery')
            msg.setParam('userId', userId)
            msg.setParam('orderId', orderId)
            msg.setParam('prodCount', count)
            msg.setParam('prodId', prodId)
            msg.setParam('appId', gameId)
            msg.setParam('orderPlatformId', '')
            msg.setParam('ok', '1')
            isSub = runhttp.getParamInt('is_msgnthly', 0)
            if isSub:
                msg.setParam('isSub', isSub)
            chargeType, chargeMap, consumeMap = HttpGameHandler.getChargeInfos()
            msg.setParam('consumeMap', consumeMap)
            msg.setParam('chargeMap', chargeMap)
            msg.setParam('chargeType', chargeType)
            return router.queryUtilServer(msg, userId)
        
#             mo = StoreTcpHandler.deliveryProduct(gameId, userId, orderId, prodId,
#                                                  chargeType, chargeMap, consumeMap, isSub)
#             return mo.pack()
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
        
    @markHttpMethod(httppath='/gtest/gamelist2/query')
    def doQueryGameList2(self, gameId, userId, clientId):
        try:
            template = hallgamelist2.getUITemplate(gameId, userId, clientId)
            games, pages = HallHelper.encodeHallUITemplage(gameId, userId, clientId, template)
            return self.makeResponse({'games':games, 'pages':pages})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
        
    @markHttpMethod(httppath='/gtest/dcheckin/status')
    def doDCheckinStatus(self, userId):
        try:
            states = halldailycheckin.dailyCheckin.getStates(HALL_GAMEID, userId, pktimestamp.getCurrentTimestamp())
            return self.makeResponse({'states':TodoTaskHelper.translateDailyCheckinStates(states)})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
        
    @markHttpMethod(httppath='/gtest/dcheckin/setdays')
    def doDCheckinSetDays(self, userId):
        try:
            checkinDays = runhttp.getParamInt('ndays', 1)
            reward = runhttp.getParamInt('reward', 1)
            timestamp = pktimestamp.getCurrentTimestamp()
            
            if checkinDays <= 1 and reward:
                userdata.delAttr(userId, 'firstDailyCheckin')
                userdata.delAttr(userId, 'lastDailyCheckin')
                userdata.clearUserCache(userId)
                states = halldailycheckin.dailyCheckin.getStates(HALL_GAMEID, userId, timestamp)
                return self.makeResponse({'states':TodoTaskHelper.translateDailyCheckinStates(states)})
            
            checkinDays = max(1, checkinDays)
            # 
            ft = timestamp - (checkinDays - 1) * 86400
            # 最后签到时间改为昨天
            if reward:
                lt = timestamp - 86400
            else:
                lt = timestamp
            userdata.setAttrs(userId, {'firstDailyCheckin' : ft, 'lastDailyCheckin' : lt})
            states = halldailycheckin.dailyCheckin.getStates(HALL_GAMEID, userId, timestamp)
            return self.makeResponse({'states':TodoTaskHelper.translateDailyCheckinStates(states)})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
        
    @markHttpMethod(httppath='/gtest/dcheckin/todotask')
    def doDCheckinTodoTask(self, userId):
        try:
            clientId = sessiondata.getClientId(userId)
            todotask = TodoTaskHelper.makeTodoTaskNsloginReward(HALL_GAMEID, userId, clientId)
            return self.makeResponse({'todotask':todotask.toDict()})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)
        
    @classmethod
    def fillUserBenefits(cls, userBenefits, mo):
        mo.setResult('updateDT', datetime.fromtimestamp(userBenefits.updateTime).strftime('%Y-%m-%d %H:%M:%S'))
        mo.setResult('times', userBenefits.times)
        mo.setResult('maxTimes', userBenefits.maxTimes)
        mo.setResult('sendChip', userBenefits.sendChip)
        mo.setResult('extTimes', userBenefits.extTimes)
        mo.setResult('extSendChip', userBenefits.extSendChip)
        mo.setResult('privilege', userBenefits.privilege.name if userBenefits.privilege else '')
        chip = userchip.getUserChipAll(userBenefits.userId)
        mo.setResult('canSend', userBenefits.hasLeftTimes() and chip < userBenefits.minChip)
        return mo
    
    @markHttpMethod(httppath='/gtest/user/benefits/query')
    def doQueryBenefits(self, userId):
        ftlog.info('TestHttpHandler.doQueryBenefits userId=', userId)
        timestamp = pktimestamp.getCurrentTimestamp()
        userBenefits = hallbenefits.benefitsSystem.loadUserBenefits(9999, userId, timestamp)
        mo = MsgPack()
        mo = self.fillUserBenefits(userBenefits, mo)
        return self.makeResponse(mo._ht)
    
    @markHttpMethod(httppath='/gtest/user/benefits/send')
    def doBenefitsSend(self, userId, clientId, today):
        ftlog.info('TestHttpHandler.doQueryBenefits userId=', userId,
                   'today=', today.strftime('%Y-%m-%d'))
        timestamp = int(time.mktime(today.timetuple()))
        sent, userBenefits = hallbenefits.benefitsSystem.sendBenefits(9999, userId, timestamp)
        mo = MsgPack()
        mo = self.fillUserBenefits(userBenefits, mo)
        mo.setResult('sentBenefits', sent)
        return self.makeResponse(mo._ht)
    
    @markHttpMethod(httppath='/gtest/user/benefits/setTimes')
    def doBenefitsSetTimes(self, userId, times):
        ftlog.info('TestHttpHandler.doQueryBenefits userId=', userId)
        timestamp = pktimestamp.getCurrentTimestamp()
        d = {'ut':int(time.time()), 'times':times}
        gamedata.setGameAttr(userId, 9999, 'benefits', json.dumps(d))
        userBenefits = hallbenefits.benefitsSystem.loadUserBenefits(9999, userId, timestamp)
        mo = MsgPack()
        mo = self.fillUserBenefits(userBenefits, mo)
        return self.makeResponse(mo._ht)
    
    def _encodeSubMemberStatus(self, status):
        return {'isSub':status.isSub,
                'subTime':status.subDT.strftime('%Y-%m-%d %H:%M:%S') if status.subDT else None,
                'deliveryDT':status.deliveryDT.strftime('%Y-%m-%d %H:%M:%S') if status.deliveryDT else None,
                'unsubDesc':status.unsubDesc}
        
    @markHttpMethod(httppath='/gtest/user/subMember/getInfo')
    def doSubMemberGetInfo(self, userId):
        status = hallsubmember.loadSubMemberStatus(userId)
        return self.makeResponse(self._encodeSubMemberStatus(status))
        
    def _check_param_isSub(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value not in (0, 1):
            return self.makeErrorResponse(-1, 'isSub必须是0或1的整数'), None
        return None, value
    
    def _check_param_unsubDesc(self, key, params):
        value = runhttp.getParamStr(key, '')
        return None, value
    
    def _check_param_subTime(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return None, None
        return None, datetime.strptime(value, '%Y-%m-%d')
    
    def _check_param_deliveryTime(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return None, None
        return None, datetime.strptime(value, '%Y-%m-%d')
    
    def _check_param_isTempVipUser(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value not in (0, 1):
            return self.makeErrorResponse(-1, 'isTempVipUser必须是0或1的整数'), None
        return None, value
    
    @markHttpMethod(httppath='/gtest/user/subMember/setSubInfo')
    def doSubMemberSetSubInfo(self, userId, isSub, unsubDesc):
        userdata.setAttrs(userId, {'isYouyifuVipUser' : 1 if isSub else 0, 'youyifuVipMsg' : unsubDesc})
        status = hallsubmember.loadSubMemberStatus(userId)
        return self.makeResponse(self._encodeSubMemberStatus(status))
        
    @markHttpMethod(httppath='/gtest/user/subMember/setTimeInfo')
    def doSubMemberSetTimeInfo(self, userId, subTime, deliveryTime):
        status = hallsubmember.loadSubMemberStatus(userId)
        status.subDT = subTime
        status.deliveryDT = deliveryTime
        hallsubmember._saveSubMemberStatus(userId, status)
        return self.makeResponse(self._encodeSubMemberStatus(status))
            
    @markHttpMethod(httppath='/gtest/user/subMember/unsub')
    def doSubMemberUnsub(self, userId, isTempVipUser):
        timestamp = pktimestamp.getCurrentTimestamp()
        userdata.delAttr(userId, 'isYouyifuVipUser')
        userdata.delAttr(userId, 'youyifuVipMsg')
        userdata.clearUserCache(userId)
        hallsubmember.unsubscribeMember(HALL_GAMEID, userId, isTempVipUser, timestamp, 'TEST_ADJUST', 0)
        status = hallsubmember.loadSubMemberStatus(userId)
        return self.makeResponse(self._encodeSubMemberStatus(status))
    
    def _check_param_fiveStarDesc(self, key, params):
        value = runhttp.getParamStr(key, '')
        return None, value
    
    @markHttpMethod(httppath='/gtest/fiveStar/triggle')
    def doTriggleFiveStarRate(self, userId, fiveStarDesc, clientId):
        timestamp = pktimestamp.getCurrentTimestamp()
        if not clientId:
            clientId = sessiondata.getClientId(userId)
        if not fiveStarDesc:
            fiveStarDesc = configure.getGameJson(6, 'public', {}).get('five_star_win_desc', '')
        _triggled, todotask = fivestarrate.triggleFiveStarRateIfNeed(userId, clientId, timestamp, fiveStarDesc)
        if todotask:
            return self.makeResponse({'todotask':todotask.toDict()})
        return self.makeResponse({})
    
    @markHttpMethod(httppath='/gtest/fiveStar/clear')
    def doClearFiveStarRate(self, userId, fiveStarDesc, clientId):
        if not clientId:
            clientId = sessiondata.getClientId(userId)
        fivestarrate.clearFiveStarRate(userId, clientId)
        return self.makeResponse({})
    
    @markHttpMethod(httppath='/gtest/generateExcode')
    def doGenExcode(self):
        paramsDict = runhttp.getDict()
        mo = TYActivityExchangeCode.doGenerateCode(paramsDict)
        return self.makeResponse(mo._ht) 

    @markHttpMethod(httppath='/gtest/neituiguang/queryState')
    def doNeituiguangQueryState(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'query_state')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/checkCode')
    def doNeituiguangCheckCode(self, userId, promoteCode, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'code_check')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        msg.setParam('promoteCode', promoteCode)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/listInvitee')
    def doNeituiguangListInvitee(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'list_invitee')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/cancelCheckCode')
    def doNeituiguangCancelCheckCode(self, userId, promoteCode, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'cancel_code_check')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/queryTaskInfo')
    def doNeituiguangQueryTaskInfo(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'query_task_info')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/getTaskReward')
    def doNeituiguangGetTaskReward(self, userId, taskId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'get_task_reward')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        msg.setParam('taskId', taskId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/queryPrize')
    def doNeituiguangQueryPrize(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'query_prize')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    @markHttpMethod(httppath='/gtest/neituiguang/getPrize')
    def doNeituiguangGetPrize(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'get_prize')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)
    
    
    @markHttpMethod(httppath='/gtest/firstRecharge/query')
    def doFirstRechargeQuery(self, userId, clientId, gameId):
        itemId = hall_first_recharge.queryFirstRecharge(gameId, userId, clientId)
        return itemId
    
    @markHttpMethod(httppath='/gtest/addExitNotification')
    def doAddExitNotification(self, userId, time, dsc):
        todotask = TodoTaskAddExitNotification(dsc, time)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todotask)
    
    @markHttpMethod(httppath='/gtest/openThirdApp')
    def doOpenThirdAPp(self, packageName, scheme, appCode, downloadUrl, downloadType, MD5, userId):
        url = base64.b64decode(downloadUrl)
        todoTask = TodoTaskDownloadOrOpenThirdApp(packageName, scheme, url, downloadType, appCode, MD5)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todoTask);
    
    @markHttpMethod(httppath='/gtest/vipLevelUp')
    def doVipLevelUp(self, userId):
        vipInfo = {"level":1, "name":"VIP0", "exp":50, "expCurrent":50, "expNext":100}
        desc = "VIPLEVELUP"
        todoTask = TodoTaskVipLevelUp(vipInfo, desc)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todoTask);
    
    @markHttpMethod(httppath='/gtest/triggerEvent')
    def doTriggerEvent(self, userId, event):
        params = {}
        todoTask = TodoTaskTriggerEvent(event, params)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todoTask);

    @markHttpMethod(httppath='/gtest/sendLed')
    def doSendLed(self, gameId, scope, led):
        mo = MsgPack()
        mo.setCmd('send_led')
        mo.setParam('msg', led)
        mo.setParam('gameId', gameId)
        mo.setParam('ismgr', 1)
        mo.setParam('scope', scope)
        mo.setParam('clientIds', [])
        router.sendToAll(mo, gdata.SRV_TYPE_UTIL)
        hallled.sendLed(gameId, led, 1, scope)
        return mo
    
    @markHttpMethod(httppath='/gtest/thirdSDKExtend')
    def doThirdSDKExtend(self, userId, action):
        todotask = TodoTaskThirdSDKExtend(action)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todotask);
    
    @markHttpMethod(httppath='/gtest/getShareUrl')
    def doGetShareUrl(self, userId, shareId):
        from hall.entity import hallshare
        share = hallshare.findShare(int(shareId))
        return share.getUrl(9999, userId)
    
    @markHttpMethod(httppath='/gtest/getDashifen')
    def doGetDashifen(self, userId, clientId):
        info = hallaccount.getGameInfo(userId, clientId)
        return info
    
    @markHttpMethod(httppath='/gtest/getShareId')
    def getShareId(self, userId, gameId, event):
        from hall.entity import hallshare
        info = hallshare.getShareId(event, userId, gameId)
        return info

    @markHttpMethod(httppath='/gtest/free/queryTask')
    def do_free_query_task(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('game')
        msg.setParam('action', 'query_task')
        msg.setParam('gameId', 9999)
        msg.setParam('clientId', clientId)
        msg.setParam('userId', userId)
        return router.queryUtilServer(msg, userId)

    @markHttpMethod(httppath='/gtest/free/getTaskReward')
    def do_free_get_task_reward(self, userId, taskId, clientId):
        msg = MsgPack()
        msg.setCmd('game')
        msg.setParam('action', 'get_task_reward')
        msg.setParam('userId', userId)
        msg.setParam('gameId', 9999)
        msg.setParam('clientId', clientId)
        msg.setParam('taskid', taskId)
        return router.queryUtilServer(msg, userId)

    def _check_param_progress(self, key, params):
        progress = runhttp.getParamInt(key, 0)
        if progress < 0:
            return self.makeErrorResponse(-1, '进度值不能是负数'), None
        return None, progress

    @markHttpMethod(httppath='/gtest/free/setTaskProgress')
    def do_task_setProgress(self, userId, taskId, progress, clientId):
        return user_remote.free_set_task_progress(userId, taskId, progress, clientId)

    @markHttpMethod(httppath='/gtest/testDomainReplace')
    def do_domain_replace(self, downloadUrl):
        url = base64.b64decode(downloadUrl)
        return halldomains.replacedDomain(url, {})
    
    @markHttpMethod(httppath='/gtest/store/chargeNotify')
    def doTestChargeNotify(self, gameId, userId, productId, rmbs, diamonds, clientId):
        clientId = clientId or sessiondata.getClientId(userId)
        mo = MsgPack()
        mo.setCmd('charge_notify')
        mo.setParam('gameId', gameId)
        mo.setParam('userId', userId)
        mo.setParam('prodId', productId)
        mo.setParam('rmbs', rmbs)
        mo.setParam('diamonds', diamonds)
        mo.setParam('clientId', clientId)
        router.sendUtilServer(mo, userId)
        return 'success'
    
    @markHttpMethod(httppath='/gtest/update/getGameUpdateInfo')
    def doGetGameUpdateInfo(self, gameId, userId, clientId, version, updateVersion):
        hall_game_update.getUpdateInfo(gameId, userId, clientId, version, updateVersion)
        
    @markHttpMethod(httppath='/gtest/testRoulette')
    def doTestRoulette(self, userId, gameId, clientId, count):
        reStr = ''
        total = 0
        for _num in range(0, count):
            number = 1
            if _num % 3 == 1:
                number = 10
            elif _num % 3 == 2:
                number = 50
                
            reStr += ' ' + str(number)
            total += number
            hallroulette.doGoldLottery(userId, gameId, clientId, number)

        return reStr + ' total:' + str(total)

    @markHttpMethod(httppath='/gtest/activity/credit_query')
    def do_activity_credit_query(self, userId, gameId, clientId, activityId):
        msg = MsgPack()
        msg.setCmd('act')
        msg.setParam('action', 'credit_query')
        msg.setParam('userId', userId)
        msg.setParam('gameId', gameId)
        msg.setParam('clientId', clientId)
        msg.setParam('activityId', activityId)
        return router.queryUtilServer(msg, userId)

    @markHttpMethod(httppath='/gtest/activity/credit_exchange')
    def do_activity_credit_exchange(self, userId, gameId, clientId, activityId, itemId):
        msg = MsgPack()
        msg.setCmd('act')
        msg.setParam('action', 'credit_exchange')
        msg.setParam('userId', userId)
        msg.setParam('gameId', gameId)
        msg.setParam('clientId', clientId)
        msg.setParam('activityId', activityId)
        msg.setParam('productId', itemId)
        return router.queryUtilServer(msg, userId)
    
    @markHttpMethod(httppath='/gtest/newzhuanyun')
    def do_test_new_zhuanyun(self, userId, gameId, clientId, event):
        timestamp = pktimestamp.getCurrentTimestamp()
        benefitsSend, userBenefits = hallbenefits.benefitsSystem.sendBenefits(gameId, userId, timestamp)
        zhuanyun = hallpopwnd.makeTodoTaskZhuanyunByLevelName(gameId, userId, clientId, benefitsSend, userBenefits, event)
        if zhuanyun  :
            return TodoTaskHelper.sendTodoTask(gameId, userId, zhuanyun)

    @markHttpMethod(httppath='/gtest/friendTableInfo')
    def do_get_friend_table_info(self, roomId0):
        roomIdStr = hall_friend_table.getStringFTId(roomId0)
        pluginId = hall_friend_table.queryFriendTable(roomIdStr)
        if not pluginId:
            return 'None game use ftId:', roomIdStr
        return pluginId
    
    @markHttpMethod(httppath='/gtest/createFriendTable')
    def do_create_friend_table(self, gameId):
        ftId = hall_friend_table.createFriendTable(gameId)
        if not ftId:
            return 'No suitable ftId created, please get one more'
        return ftId
    
    @markHttpMethod(httppath='/gtest/queryFangKaItem')
    def do_query_fangka_item(self, userId, clientId):
        return hall_fangka.queryFangKaItem(9999, userId, clientId)
    
    @markHttpMethod(httppath='/gtest/queryWXAppid')
    def do_query_wxappid(self, userId, clientId):
        return hall_wxappid.queryWXAppid(9999, userId, clientId)
    
    @markHttpMethod(httppath='/gtest/queryFangKaBuyInfo')
    def do_query_fangKaBuyInfo(self, userId, clientId):
        return hall_fangka_buy_info.queryFangKaBuyInfo(9999, userId, clientId)
    
    @markHttpMethod(httppath='/gtest/hall/cond/check')
    def doCheckCondition(self, gameId, userId, clientId):
        value = runhttp.getParamStr('condition')
        if not value:
            return self.makeErrorResponse(-1, '必须指定有效的cond')
        try:
            d = strutil.loads(value)
            cond = UserConditionRegister.decodeFromDict(d)
            ret = cond.check(gameId, userId, clientId, pktimestamp.getCurrentTimestamp())
            return self.makeResponse(ret)
        except:
            ftlog.error('doCheckCondition',
                        'gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId)
            return self.makeErrorResponse(-1, '必须指定有效的cond')

    def _check_param_deadline(self, key, params):
        interval = runhttp.getParamInt(key, 0)
        if interval <= 0:
            return self.makeErrorResponse(-1, '时长必须是正数'), None
        return None, interval

    def _check_param_notice(self, key, params):
        notice = runhttp.getParamStr(key, 0)
        if not notice:
            return self.makeErrorResponse(-1, '必须有通知文本'), None
        return None, notice

    def _check_param_sharePointId(self, key, params):
        value = runhttp.getParamInt(key)
        if value is None:
            return self.makeErrorResponse(-1, '分享点id必须是整数'), None
        return None, value

    def _check_param_pointId(self, key, params):
        value = runhttp.getParamInt(key)
        if value is None:
            return self.makeErrorResponse(-1, '分享点id必须是整数'), None
        return None, value
    
    @markHttpMethod(httppath='/gtest/alarm/register')
    def do_alarm_register(self, userId, gameId, deadline, notice):
        return user_remote.registerAlarm(userId, gameId, deadline + pktimestamp.getCurrentTimestamp(), notice)

    @markHttpMethod(httppath='/gtest/alarm/query')
    def do_alarm_query(self, userId):
        return user_remote.queryAlarm(userId)

    @markHttpMethod(httppath='/gtest/roulette/gold')
    def doTestRoulette2(self, userId, gameId, clientId, count):
        hallroulette.doGoldLottery(userId, gameId, clientId, count)

    @markHttpMethod(httppath='/gtest/roulette/soldierhistory')
    def doSoldierHistory(self, userId, gameId, clientId):
        return hallroulette.doGetBeforeReward(userId, gameId, clientId)
    
    @markHttpMethod(httppath='/gtest/hall/exmall/shelves/list')
    def doTestExMallGetShelves(self, userId, clientId):
        mo = exmall_handler.HallExMallHandler._doGetShelves(HALL_GAMEID, userId, clientId)
        return mo._ht
    
    def _check_param_shelvesName(self, key, params):
        value = runhttp.getParamStr(key)
        if not value:
            return self.makeErrorResponse(-1, '必须指定shelvesName'), None
        return None, value
    
    def _check_param_queryExchangeId(self, key, params):
        value = runhttp.getParamStr('exchangeId', '')
        if not isstring(value):
            return self.makeErrorResponse(-1, '必须指定exchangeId'), None
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/exmall/stock/query')
    def doTestExMallQueryStock(self, queryExchangeId):
        if queryExchangeId:
            stockObj = hall_exmall.getStock(queryExchangeId, pktimestamp.getCurrentTimestamp())
            return {'exchangeId':queryExchangeId, 'stock':stockObj.stock,
                    'checksum':stockObj.checksum, 'lastUpdateTime':stockObj.lastUpdateTime,
                    'issueNum':stockObj.issueNum}
        else:
            stockObjMap = hall_exmall.loadAllStockObj()
            ret = []
            for exchangeId, stockObj in stockObjMap.iteritems():
                ret.append({'exchangeId':exchangeId, 'stock':stockObj.stock,
                            'checksum':stockObj.checksum, 'lastUpdateTime':stockObj.lastUpdateTime,
                            'issueNum':stockObj.issueNum})
            return ret
    
    @markHttpMethod(httppath='/gtest/hall/exmall/exchange/list')
    def doTestExMallGetProduct(self, userId, clientId, shelvesName):
        mo = exmall_handler.HallExMallHandler._doGetProduct(HALL_GAMEID, userId, clientId,
                                                            shelvesName, pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/exmall/exchange/exchange')
    def doTestExMallExchange(self, userId, clientId, exchangeId, exchangeCount, exchangeParams):
        ftlog.debug('TestHttpHandler.doTestExMallExchange',
                    'userId=', userId,
                    'clientId=', clientId,
                    'exchangeId=', exchangeId,
                    'exchangeCount=', exchangeCount,
                    'exchangeParams=', exchangeParams)
        mo = exmall_handler.HallExMallHandler._doExchange(HALL_GAMEID, userId, clientId,
                                                          exchangeId, exchangeCount, exchangeParams,
                                                          pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    @classmethod
    def encodeOrder(cls, order):
        return {
            'orderId':order.orderId,
            'exchangeId':order.exchangeId,
            'count':order.count,
            'cost':order.cost,
            'state':order.state,
            'params':order.params,
            'createTime':datetime.fromtimestamp(order.createTime).strftime('%Y-%m-%d %H:%M:%S'),
            'errorCode':order.errorCode,
            'clientId':order.clientId,
            'deliveryInfo':order.deliveryInfo
        }
    
    def _check_param_queryOrderId(self, key, params):
        orderId = runhttp.getParamStr('orderId', '')
        if not isstring(orderId):
            return self.makeErrorResponse(-1, '必须指定orderId'), None
        return None, orderId
    
    @markHttpMethod(httppath='/gtest/hall/exmall/order/query')
    def doTestExMallOrderList(self, userId, clientId, queryOrderId):
        if queryOrderId:
            order = hall_exmall.loadOrder(userId, queryOrderId)
            return self.encodeOrder(order)
        else:
            orderMap = hall_exmall.loadAllOrder(userId)
            ret = []
            for _, order in orderMap.iteritems():
                ret.append(self.encodeOrder(order))
            return ret

    def _check_param_auditResult(self, key, params):
        value = runhttp.getParamInt(key, 0)
        return None, value
    
    def _check_param_shippingResult(self, key, params):
        value = runhttp.getParamInt(key, 0)
        return None, value
    
    def _check_param_jdOrderId(self, key, params):
        value = runhttp.getParamStr(key)
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/exmall/order/audit')
    def doTestExMallOrderAudit(self, userId, clientId, orderId, auditResult):
        ec, info = hall_exmall_remote.handleAuditResult(HALL_GAMEID, userId, orderId, auditResult)
        if ec != 0:
            return {'ec':ec, 'info':info}
        order = hall_exmall.loadOrder(userId, orderId)
        return self.encodeOrder(order)

    @markHttpMethod(httppath='/gtest/hall/exmall/order/shipping')
    def doTestExMallOrderShipping(self, userId, clientId, orderId, shippingResult, jdOrderId):
        ec, info = hall_exmall_remote.handleShippingResult(HALL_GAMEID, userId, orderId, shippingResult, jdOrderId)
        if ec != 0:
            return {'ec':ec, 'info':info}
        order = hall_exmall.loadOrder(userId, orderId)
        return self.encodeOrder(order)
    
    @markHttpMethod(httppath='/gtest/hall/exmall/order/auditAndShipping')
    def doTestExMallOrderAuditAndShipping(self, userId, clientId, orderId, jdOrderId):
        ec, info = hall_exmall_remote.handleAuditResult(HALL_GAMEID, userId, orderId, hall_exmall.RESULT_AUDITSUCC)
        if ec == 0:
            ec, info = hall_exmall_remote.handleShippingResult(HALL_GAMEID, userId, orderId, hall_exmall.RESULT_OK, jdOrderId)
        
        if ec != 0:
            return {'ec':ec, 'info':info}
        order = hall_exmall.loadOrder(userId, orderId)
        return self.encodeOrder(order)

    def _check_param_curTime(self, key, params):
        value = runhttp.getParamStr(key)
        if not value:
            return None, pktimestamp.getCurrentTimestamp()
        if not isstring(value):
            return self.makeErrorResponse(-1, '当前时间格式错误'), None
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return None, pktimestamp.datetime2Timestamp(dt)
        except:
            return self.makeErrorResponse(-1, '当前时间格式错误'), None
    
    def _check_param_shareLoc(self, key, params):
        value = runhttp.getParamStr(key)
        return None, value
    
    def _check_param_rewardCount(self, key, params):
        value = runhttp.getParamInt(key, 0)
        return None, value
    
    def _check_param_intShareId(self, key, params):
        value = runhttp.getParamInt('shareId', 0)
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/share/setStatus')
    def setShareStatus(self, userId, intShareId, curTime, rewardCount):
        from hall.entity import hallshare
        share = hallshare.findShare(intShareId)
        if not share:
            return {'ec':-1, 'info':'Not found shareId: %s' % (intShareId)}
        hallshare.saveShareStatus(userId, share, curTime, rewardCount)
        return {'lastUpdateTime':pktimestamp.formatTimeSecond(datetime.fromtimestamp(curTime)),
                'rewardCount':rewardCount}
        
    @markHttpMethod(httppath='/gtest/hall/share/getStatus')
    def getShareStatus(self, userId, intShareId, curTime):
        from hall.entity import hallshare
        share = hallshare.findShare(intShareId)
        if not share:
            return {'ec':-1, 'info':'Not found shareId: %s' % (intShareId)}
        shareTime, rewardCount = hallshare.getShareStatus(userId, share, curTime)
        return {'lastUpdateTime':pktimestamp.formatTimeSecond(datetime.fromtimestamp(shareTime)),
                'rewardCount':rewardCount}
        
    @markHttpMethod(httppath='/gtest/hall/share/getReward')
    def getShareReward(self, userId, intShareId, shareLoc, curTime):
        from hall.entity import hallshare
        share = hallshare.findShare(intShareId)
        if not share:
            return {'ec':-1, 'info':'Not found shareId: %s' % (intShareId)}
        ret = hallshare.getShareReward(HALL_GAMEID, userId, share, shareLoc, curTime)
        shareTime, rewardCount = hallshare.getShareStatus(userId, share, curTime)
        return {'reward':ret,
                'lastUpdateTime':pktimestamp.formatTimeSecond(datetime.fromtimestamp(shareTime)),
                'rewardCount':rewardCount}

    @markHttpMethod(httppath='/gtest/popwnd/diamond2coin')
    def testDiamond2coin(self, userId, gameId, clientId):
        task = hallpopwnd.makeTodoTaskDiamondToCoin(gameId, userId, clientId, 23456, 'dis', 12, False, 2)
        return task.toDict()
    
    @markHttpMethod(httppath='/gtest/hall/share2/sendShare')
    def share2SendShare(self, gameId, userId, clientId, sharePointId, urlParams):
        todotask = hall_share2.buildShareTodoTask(gameId, userId, clientId, sharePointId, urlParams)
        if not todotask:
            return {'ec':-1, 'info':'Not found sharePointId: %s' % (sharePointId)}
        TodoTaskHelper.sendTodoTask(gameId, userId, todotask)
        return todotask.toDict()
    
    @markHttpMethod(httppath='/gtest/hall/share2/getShare')
    def share2GetShare(self, gameId, userId, clientId, sharePointId, urlParams):
        mp = Share2TcpHandler._doGetShareInfo(gameId, userId, clientId, sharePointId, urlParams)
        if not mp:
            return {'ec':-1, 'info':'Not found sharePointId: %s' % (sharePointId)}
        return mp._ht
    
    @markHttpMethod(httppath='/gtest/hall/share2/getShareUrl')
    def share2GetShareUrl(self, gameId, userId, clientId, sharePointId, intShareId, urlParams):
        mp = Share2TcpHandler._doGetShareUrl(gameId, userId, clientId, sharePointId, intShareId, urlParams)
        if not mp:
            return {'ec':-1, 'info':'Not found %s:%s: %s' % (sharePointId, intShareId)}
        return mp._ht
    
    @markHttpMethod(httppath='/gtest/hall/share2/rewardStatus')
    def share2RewardStatus(self, gameId, userId, clientId, sharePointId, curTime):
        parsedClientId = ParsedClientId.parseClientId(clientId)
        if not parsedClientId:
            return {'ec':-1, 'info':'Bad clientId'}
        sharePoint = hall_share2.getSharePoint(gameId, parsedClientId, sharePointId)
        ts, count = hall_share2.loadShareStatus(gameId, userId, sharePoint, curTime)
        return {'time':datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), 'count':count}

    @markHttpMethod(httppath='/gtest/hall/share2/setRewardStatus')
    def share2SetRewardStatus(self, gameId, userId, clientId, sharePointId, curTime, count):
        hall_share2.saveShareStatus(gameId, userId, sharePointId, curTime, count)
        return {'time':datetime.fromtimestamp(curTime).strftime('%Y-%m-%d %H:%M:%S'), 'count':count}
    
    @markHttpMethod(httppath='/gtest/hall/share2/gainReward')
    def share2GainReward(self, gameId, userId, clientId, sharePointId, curTime):
        mp = Share2TcpHandler._doGetShareReward(gameId, userId, clientId, sharePointId)
        return mp._ht

    @markHttpMethod(httppath='/gtest/hall/yybgift/list')
    def yybgiftList(self, userId, curTime):
        userGiftStatusMap = hall_yyb_gifts.loadAndInitUserGifts(userId, curTime)
        ret = []
        for kindId, status in userGiftStatusMap.iteritems():
            d = status.toDict()
            d['kindId'] = kindId
            d['state'] = hall_yyb_gifts.calcState(status)
            ret.append(d)
        return ret

    def _check_param_giftKindId(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value == 0:
            return self.makeErrorResponse(-1, '必须指定礼包类型'), None
        return None, value
    
    def _check_param_finishTime(self, key, params):
        value = runhttp.getParamStr(key)
        if not value:
            return None, 0
        if not isstring(value):
            return self.makeErrorResponse(-1, '完成时间格式错误'), None
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return None, pktimestamp.datetime2Timestamp(dt)
        except:
            return self.makeErrorResponse(-1, '完成时间格式错误'), None
    
    def _check_param_gainTime(self, key, params):
        value = runhttp.getParamStr(key)
        if not value:
            return None, 0
        if not isstring(value):
            return self.makeErrorResponse(-1, '领取时间格式错误'), None
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return None, pktimestamp.datetime2Timestamp(dt)
        except:
            return self.makeErrorResponse(-1, '领取时间格式错误'), None
    
    def _check_param_lastUpdateTime(self, key, params):
        value = runhttp.getParamStr(key)
        if not value:
            return None, pktimestamp.getCurrentTimestamp()
        if not isstring(value):
            return self.makeErrorResponse(-1, '最后更新时间格式错误'), None
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return None, pktimestamp.datetime2Timestamp(dt)
        except:
            return self.makeErrorResponse(-1, '最后更新时间格式错误'), None
    
    @markHttpMethod(httppath='/gtest/hall/yybgift/setStatus')
    def yybgiftSetStatus(self, userId, giftKindId, finishTime, gainTime, lastUpdateTime, progress):
        d = {'ft':finishTime, 'gt':gainTime, 'lut':lastUpdateTime, 'prog':progress}
        jstr = strutil.dumps(d)
        daobase.executeUserCmd(userId, 'hset', 'yyb.gifts:%s' % (userId), giftKindId, jstr)
        return d
    
    @markHttpMethod(httppath='/gtest/hall/yybgift/gainReward')
    def yybgiftGainReward(self, userId, giftKindId, curTime):
        ec, res = hall_yyb_gifts_remote.gainYYBGift(userId, giftKindId, curTime)
        if ec == 0:
            return {'code':res}
        return {'code':-1, 'info':res}

    @markHttpMethod(httppath='/gtest/hall/evalSimulate')
    def testEvalSimulate(self):
        gameId = runhttp.getParamInt('gameId')
        userId = runhttp.getParamInt('userId')
        context = runhttp.getParamStr('context')

        ftlog.info('testEvalSimulate gameId=', gameId,
                   'userId=', userId,
                   'context=', context
                   )
        try:
            msg = MsgPack()
            msg.setCmd('hall')
            msg.setResult('action', 'evalSimulate')
            msg.setResult('gameId', gameId)
            msg.setResult('userId', userId)
            msg.setResult('context', context)
            router.sendToUser(msg, userId)

            return {'gameId': gameId, 'userId': userId, 'context': context}
        except Exception, e:
            if not isinstance(e, TYBizException):
                ftlog.error()
            ec, info = (e.errorCode, e.message) if isinstance(e, TYBizException) else (-1, '参数错误')

            ftlog.warn('testEvalSimulate.error',
                       'gameId=', gameId,
                       'userId=', userId,
                       'context=', context,
                       'ec=', ec,
                       'info=', info)

            return {'ec': ec, 'info': info}

    @markHttpMethod(httppath='/gtest/hall/addMatchNotify')
    def testAddMatchNotify(self):
        gameId = runhttp.getParamInt('gameId')
        gameType = runhttp.getParamInt('gameType')
        matchIndex = runhttp.getParamInt('matchIndex')
        userId = runhttp.getParamInt('userId')
        matchName = runhttp.getParamStr('matchName')
        matchDesc = runhttp.getParamStr('matchDesc')
        matchIcon = runhttp.getParamStr('matchIcon')
        signinFee = runhttp.getParamStr('signinFee')
        timestamp = runhttp.getParamInt('timestamp')
        notifyType = runhttp.getParamInt('notifyType')
        matchId = runhttp.getParamInt('matchId')

        if ftlog.is_debug():
            ftlog.debug('testAddMatchNotify gameId=', gameId,
                        'gameType=', gameType,
                        'matchIndex=', matchIndex,
                        'userId=', userId,
                        'matchName=', matchName,
                        'matchDesc=', matchDesc,
                        'matchIcon=', matchIcon,
                        'signinFee=', signinFee,
                        'timestamp=', timestamp,
                        'notifyType=', notifyType,
                        'matchId=', matchId)

        from hall.servers.util.rpc import match_remote
        match_remote.sendMatchNotify(gameId, userId, matchName, matchDesc, matchIcon, signinFee, timestamp, matchId,
                                     notifyType, gameType, matchIndex)

    @markHttpMethod(httppath='/gtest/hall/clearatchNotify')
    def testClearatchNotify(self):
        userId = runhttp.getParamInt('userId')

        from hall.entity import hallnewnotify
        return hallnewnotify.clearAllMatchNotify(userId)

    @markHttpMethod(httppath='/gtest/hall/duobao/bet')
    def testDuobaoBet(self):
        userId = runhttp.getParamInt('userId')
        duobaoId = runhttp.getParamStr('duobaoId')
        issue = runhttp.getParamInt('issue')
        num = runhttp.getParamInt('num')

        from hall.servers.util.rpc import duobao_remote
        return duobao_remote.duobaoBet(userId, duobaoId, issue, num)

    @markHttpMethod(httppath='/gtest/hall/duobao/reward')
    def testDuobaoReward(self):
        userId = runhttp.getParamInt('userId')
        duobaoId = runhttp.getParamStr('duobaoId')
        issue = runhttp.getParamInt('issue')

        from hall.servers.util.rpc import duobao_remote
        return duobao_remote.duobaoReward(userId, duobaoId, issue)

    @markHttpMethod(httppath='/gtest/hall/duobao/product')
    def testDuobaoProduct(self):
        userId = runhttp.getParamInt('userId')

        from hall.servers.util.rpc import duobao_remote
        return duobao_remote.duobaoProduct(userId)

    @markHttpMethod(httppath='/gtest/hall/duobao/history')
    def testDuobaoHistory(self):
        userId = runhttp.getParamInt('userId')
        duobaoId = runhttp.getParamStr('duobaoId')
        pageId = runhttp.getParamInt('pageId')

        from hall.servers.util.rpc import duobao_remote
        return duobao_remote.duobaoHistory(userId, duobaoId, pageId)

    @markHttpMethod(httppath='/gtest/hall/duobao/record')
    def testDuobaoRecord(self):
        userId = runhttp.getParamInt('userId')
        pageId = runhttp.getParamInt('pageId')

        from hall.servers.util.rpc import duobao_remote
        return duobao_remote.duobaoRecord(userId, pageId)

    @markHttpMethod(httppath='/gtest/hall/duobao/rewardrecord')
    def testDuobaoRewardRecord(self):
        userId = runhttp.getParamInt('userId')

        from hall.servers.util.rpc import duobao_remote
        return duobao_remote.duobaoRewardRecord(userId)

    @markHttpMethod(httppath='/gtest/hall/duobao/clearall')
    def testDuobaoClearall(self):
        userId = runhttp.getParamInt('userId')

        from hall.servers.center.rpc import test
        return test.testDuobaoClearall(userId)

    @markHttpMethod(httppath='/gtest/hall/sport/product')
    def testSportProduct(self):
        userId = runhttp.getParamInt('userId')

        from hall.entity import hallsportlottery
        return hallsportlottery.sportlotteryProduct(userId)

    @markHttpMethod(httppath='/gtest/hall/sport/detail')
    def testSportDetail(self):
        userId = runhttp.getParamInt('userId')
        date = runhttp.getParamStr('date')
        uuid = runhttp.getParamInt('uuid')
        type = runhttp.getParamInt('type')

        from hall.entity import hallsportlottery
        return hallsportlottery.sportlotteryDetail(userId, date, uuid, type)

    @markHttpMethod(httppath='/gtest/hall/sport/bet')
    def testSportBet(self):
        userId = runhttp.getParamInt('userId')
        date = runhttp.getParamStr('date')
        uuid = runhttp.getParamInt('uuid')
        party = runhttp.getParamInt('party')
        coin = runhttp.getParamInt('coin')

        from hall.entity import hallsportlottery
        from poker.entity.dao import sessiondata
        return hallsportlottery.sportlotteryBet(HALL_GAMEID, sessiondata.getClientId(userId), userId, date, uuid, party, coin)

    @markHttpMethod(httppath='/gtest/hall/sport/love')
    def testSportLove(self):
        userId = runhttp.getParamInt('userId')
        date = runhttp.getParamStr('date')
        uuid = runhttp.getParamInt('uuid')
        love = runhttp.getParamInt('love')

        from hall.entity import hallsportlottery
        return hallsportlottery.sportlotteryLove(userId, date, uuid, love)

    @markHttpMethod(httppath='/gtest/hall/sport/mysport')
    def testSportMysport(self):
        userId = runhttp.getParamInt('userId')

        from hall.entity import hallsportlottery
        return hallsportlottery.sportlotteryRewardList(userId)

    @markHttpMethod(httppath='/gtest/hall/sport/getReward')
    def testSportGetReward(self):
        userId = runhttp.getParamInt('userId')
        date = runhttp.getParamStr('date')
        uuid = runhttp.getParamInt('uuid')

        from hall.entity import hallsportlottery
        from poker.entity.dao import sessiondata
        return hallsportlottery.sportlotteryGetReward(HALL_GAMEID, sessiondata.getClientId(userId), userId, date, uuid)


    def _check_param_rainTime(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value == 0:
            return self.makeErrorResponse(-1, '下雨时间必须是整数'), None
        return None, value

    def _check_param_danmuPos(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value <= -1:
            return self.makeErrorResponse(-1, '弹幕起始点必须是正整数'), None
        return None, value

    @markHttpMethod(httppath='/gtest/hall/redPacketRain/nextRain')
    def testRedPacketRainNextRain(self, userId, clientId):
        from hall.servers.util.rpc import red_packet_rain_remote
        ec, result = red_packet_rain_remote._testGetNextRain(userId, clientId)
        if ec == 0:
            return result
        return {'ec':ec}

    @markHttpMethod(httppath='/gtest/hall/redPacketRain/grab')
    def testRedPacketRainGrab(self, userId, clientId, rainTime):
        from hall.servers.util.rpc import red_packet_rain_remote
        ec, result = red_packet_rain_remote._testGrab(userId, clientId, rainTime)
        if ec == 0:
            return result
        return {'ec':ec}

    @markHttpMethod(httppath='/gtest/hall/redPacketRain/getResult')
    def testRedPacketRainGetResult(self, userId, clientId, rainTime):
        from hall.servers.util.rpc import red_packet_rain_remote
        ec, result = red_packet_rain_remote._testGetResult(userId, clientId, rainTime)
        if ec == 0:
            return result
        return {'ec':ec}

    @markHttpMethod(httppath='/gtest/hall/redPacketRain/getDanmu')
    def testRedPacketRainGetDanmu(self, userId, clientId, rainTime, danmuPos):
        from hall.servers.util.rpc import red_packet_rain_remote
        ec, result = red_packet_rain_remote._testGetDanmu(userId, clientId, rainTime, danmuPos)
        if ec == 0:
            return result
        return {'ec':ec}

    def _check_param_inviter(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '邀请人必须是正整数'), None
        return None, value
    
    def _check_param_invitee(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '被邀请人必须是正整数'), None
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/invite/getInviterInfo')
    def testGetInviterInfo(self, userId, clientId):
        mo = InviteTcpHandler._doInviterInfo(userId, HALL_GAMEID, clientId)
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/invite/bindInviter')
    def testInviteSetInviter(self, userId, clientId, inviter):
        mo = InviteTcpHandler._doBindInviter(userId, HALL_GAMEID, clientId, inviter)
        return mo._ht

    @markHttpMethod(httppath='/gtest/hall/invite/getInviteeInfo')
    def testGetInviteeInfo(self, userId, clientId):
        mo = InviteTcpHandler._doInviteeInfo(userId, HALL_GAMEID, clientId)
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/invite/gainInviteeReward')
    def testGetInviteeReward(self, userId, clientId, invitee):
        mo = InviteTcpHandler._doGainInviteeReward(userId, HALL_GAMEID, clientId, invitee)
        return mo._ht
    
    def _check_param_clipboardContent(self, key, params):
        value = runhttp.getParamStr(key, '')
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/invite/clipboardContent')
    def testInviteClipboardContent(self, userId, clientId, clipboardContent, isCreate):
        hall_invite_remote._testOnUserLogin(userId, clipboardContent, 1, isCreate, clientId)
        mo = InviteTcpHandler._doInviteeInfo(userId, HALL_GAMEID, clientId)
        return mo._ht
    
    def _check_param_dayFirst(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if not value in (0, 1):
            return self.makeErrorResponse(-1, 'dayFirst 必须是0或1'), None
        return None, bool(value)
    
    def _check_param_isCreate(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if not value in (0, 1):
            return self.makeErrorResponse(-1, 'isCreate 必须是0或1'), None
        return None, bool(value)
    
    @markHttpMethod(httppath='/gtest/hall/rptask/update')
    def testRPTaskUpdate(self, userId, clientId):
        mo = RedPacketTaskTcpHandler._doUpdate(userId, clientId, pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/rptask/setTask')
    def testRPTaskSetTaskInfo(self, userId, clientId, taskId, progress):
        timestamp = pktimestamp.getCurrentTimestamp()
        status = hall_red_packet_task.loadUserStatus(userId, timestamp)
        taskKind = hall_red_packet_task._rpTaskSystem.findTaskKind(taskId)
        if taskKind:
            task = taskKind.newTask(status)
            task.updateTime = timestamp
            status.task = task
            task.setProgress(progress, timestamp)
        else:
            status.task = None
        hall_red_packet_task._rpTaskSystem.saveStatus(status)
        mo = RedPacketTaskTcpHandler._doUpdate(userId, clientId, pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/rptask/gainReward')
    def testRPTaskGainReward(self, userId, clientId, taskId):
        mo = RedPacketTaskTcpHandler._doGainReward(userId, clientId, pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/rptask/bindWXOpenId')
    def testRPTaskBindWXOpenId(self, userId, clientId):
        mo = MsgPack()
        mo.setCmdAction('hall', 'bind_wx_openid')
        mo.setParam('gameId', HALL_GAMEID)
        mo.setParam('userId', userId)
        mo.setParam('openId', 'testopenId')
        router.sendUtilServer(mo, userId)
        mo = RedPacketTaskTcpHandler._doUpdate(userId, clientId, pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/rpexchange/update')
    def testRPExchangeUpdate(self, userId, clientId):
        mo = RedPacketExchangeTcpHandler._doUpdate(HALL_GAMEID, userId, clientId, pktimestamp.getCurrentTimestamp())
        return mo._ht
    
    def _check_param_rpExchangeId(self, key, params):
        value = runhttp.getParamInt('exchangeId', -1)
        if value == -1:
            return self.makeErrorResponse(-1, 'exchangeId 必须是整数'), None
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/rpexchange/exchange')
    def testRPExchangeExchange(self, userId, clientId, rpExchangeId):
        mo = RedPacketExchangeTcpHandler._doExchange(HALL_GAMEID, userId, clientId, rpExchangeId, pktimestamp.getCurrentTimestamp())
        return mo._ht

    @markHttpMethod(httppath='/gtest/hall/rpmain/update')
    def testRPMainUpdate(self, userId, clientId):
        mo = RedPacketMainTcpHandler._doUpdate(HALL_GAMEID, userId, clientId)
        return mo._ht
    
    @markHttpMethod(httppath='/gtest/hall/rpmain/gainReward')
    def testRPMainGainReward(self, userId, clientId):
        mo = RedPacketMainTcpHandler._doGainReward(HALL_GAMEID, userId, clientId)
        return mo._ht

        
    def _check_param_wxappId(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, 'wxappId 必须是非空字符串'), None
        return None, value
    
    def _check_param_cashValue(self, key, params):
        value = runhttp.getParamInt('value', 0)
        if value <= 0:
            return self.makeErrorResponse(-1, 'value 必须>0的整数'), None
        return None, value
    
    @markHttpMethod(httppath='/gtest/hall/cash/getCash')
    def testCashGetCash(self, userId, clientId, wxappId, cashValue):
        record, _ = hallexchange.requestExchangeCash(userId, cashValue, wxappId, pktimestamp.getCurrentTimestamp())
        return {'exchangeId':record.exchangeId}

    @markHttpMethod(httppath='/gtest/hall/share/control')
    def testShareControl(self, gameId, userId, pointId, whereToShare):
        from hall.servers.util.share3_handler import Share3TcpHandler
        clientId = sessiondata.getClientId(userId)
        mp = Share3TcpHandler._doGetShareReward(gameId, userId, clientId, pointId, whereToShare)
        if mp:
            router.sendToUser(mp, userId)
            return mp.pack()

    # *******************************
    #           奖券明细接口
    # *******************************
    @markHttpMethod(httppath='/gtest/hall/coupon/details')
    def doUserCouponDetails(self,  gameId, userId, clientId):
        msg = UserCouponDetailsTcpHandler._doGetUserCouponDetails(gameId, userId, clientId)
        return self.makeResponse(msg._ht)

